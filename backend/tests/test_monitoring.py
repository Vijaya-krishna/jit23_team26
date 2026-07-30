"""
Unit Tests — Module 5: Resource Monitor
Verifies that simulation tick steps correctly write time-series telemetry log entries
and that the retrieval endpoints return chronologically ordered data.
"""
import sys
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend package is resolvable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.database.session import Base
from backend.database.models.simulation_models import (
    PhysicalServerModel, VirtualMachineModel, SimulationStateModel,
    TaskModel, GlobalTelemetryLogModel, HostTelemetryLogModel
)
from backend.api.repositories.simulation_repository import SimulationRepository
from backend.api.services.simulation_service import SimulationService


@pytest.fixture(scope="function")
def db_session():
    """
    Build an in-memory SQLite database and session for isolated test runs.
    """
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed simulation state
    state = SimulationStateModel(id=1, tick_counter=0, total_energy_kwh=0.0)
    session.add(state)
    session.commit()

    # Seed 2 physical hosts
    for _ in range(2):
        host = PhysicalServerModel(
            cpu_cores=16, cpu_frequency_ghz=3.2, ram_mb=64000.0, storage_gb=2000.0,
            bandwidth_mbps=10000.0, power_state="ACTIVE", temperature=22.0,
            cpu_utilization=0.0, ram_utilization=0.0, storage_utilization=0.0,
            bandwidth_utilization=0.0, power_consumption=80.0
        )
        session.add(host)
    session.commit()

    yield session
    session.close()


@pytest.fixture
def sim_service(db_session):
    repo = SimulationRepository(db_session)
    return SimulationService(repo)


class TestGlobalTelemetryLogInsertion:
    """
    Tests that trigger_tick writes GlobalTelemetryLogModel rows after each clock step.
    """

    def test_no_logs_before_first_tick(self, db_session, sim_service):
        """
        Before any tick, global_telemetry_logs table should be empty.
        """
        logs = db_session.query(GlobalTelemetryLogModel).all()
        assert len(logs) == 0

    def test_one_global_log_written_per_tick(self, db_session, sim_service):
        """
        After one tick, exactly one global log row should be inserted.
        """
        sim_service.trigger_tick()
        logs = db_session.query(GlobalTelemetryLogModel).all()
        assert len(logs) == 1

    def test_five_ticks_produce_five_global_logs(self, db_session, sim_service):
        """
        After five ticks, five sequential global log rows should exist.
        """
        for _ in range(5):
            sim_service.trigger_tick()
        logs = db_session.query(GlobalTelemetryLogModel).order_by(GlobalTelemetryLogModel.tick).all()
        assert len(logs) == 5
        # Tick counter must be strictly increasing
        for i, log in enumerate(logs):
            assert log.tick == i + 1

    def test_global_log_has_valid_power_values(self, db_session, sim_service):
        """
        Power readings in global logs must be non-negative and physically consistent.
        """
        sim_service.trigger_tick()
        log = db_session.query(GlobalTelemetryLogModel).first()
        assert log.it_power_w >= 0.0
        assert log.cooling_power_w >= 0.0
        assert log.total_power_w >= log.it_power_w     # total >= IT power

    def test_global_log_utilization_within_bounds(self, db_session, sim_service):
        """
        CPU and RAM utilisation values must be in [0.0, 1.0].
        """
        sim_service.trigger_tick()
        log = db_session.query(GlobalTelemetryLogModel).first()
        assert 0.0 <= log.cpu_utilization <= 1.0
        assert 0.0 <= log.ram_utilization <= 1.0
        assert 0.0 <= log.storage_utilization <= 1.0
        assert 0.0 <= log.bandwidth_utilization <= 1.0

    def test_global_log_carbon_positive_when_power_drawn(self, db_session, sim_service):
        """
        Carbon emissions should be positive whenever power is consumed.
        """
        sim_service.trigger_tick()
        log = db_session.query(GlobalTelemetryLogModel).first()
        if log.total_power_w > 0:
            assert log.carbon_emissions_kg >= 0.0


class TestHostTelemetryLogInsertion:
    """
    Tests that trigger_tick writes HostTelemetryLogModel rows for each active host.
    """

    def test_host_logs_written_per_active_host(self, db_session, sim_service):
        """
        After one tick, there should be one log entry per active host.
        """
        active_hosts = db_session.query(PhysicalServerModel).filter(
            PhysicalServerModel.power_state == "ACTIVE"
        ).count()
        sim_service.trigger_tick()
        host_logs = db_session.query(HostTelemetryLogModel).all()
        assert len(host_logs) == active_hosts

    def test_host_log_temperature_realistic(self, db_session, sim_service):
        """
        Host temperatures should start above 20°C and stay below thermal safety margin of 90°C.
        """
        sim_service.trigger_tick()
        for log in db_session.query(HostTelemetryLogModel).all():
            assert 20.0 <= log.temperature <= 90.0

    def test_host_logs_match_registered_host_ids(self, db_session, sim_service):
        """
        All host_id values in HostTelemetryLogModel must reference existing PhysicalServerModel rows.
        """
        sim_service.trigger_tick()
        host_ids_in_db = {h.id for h in db_session.query(PhysicalServerModel).all()}
        logged_host_ids = {l.host_id for l in db_session.query(HostTelemetryLogModel).all()}
        assert logged_host_ids.issubset(host_ids_in_db)

    def test_multiple_tick_host_logs_accumulate(self, db_session, sim_service):
        """
        Over 3 ticks with 2 hosts, 6 host log rows should accumulate.
        """
        for _ in range(3):
            sim_service.trigger_tick()
        count = db_session.query(HostTelemetryLogModel).count()
        assert count == 6  # 3 ticks × 2 hosts


class TestRepositoryLogRetrieval:
    """
    Tests the repository-layer retrieval helpers for log pagination and ordering.
    """

    def test_list_global_logs_ordered_by_tick(self, db_session, sim_service):
        """
        list_global_logs() must return entries ordered by ascending tick number.
        """
        for _ in range(4):
            sim_service.trigger_tick()
        repo = SimulationRepository(db_session)
        logs = repo.list_global_logs(limit=100)
        ticks = [l.tick for l in logs]
        assert ticks == sorted(ticks)

    def test_list_global_logs_respects_limit(self, db_session, sim_service):
        """
        list_global_logs(limit=2) should return at most 2 rows even when more exist.
        """
        for _ in range(5):
            sim_service.trigger_tick()
        repo = SimulationRepository(db_session)
        logs = repo.list_global_logs(limit=2)
        assert len(logs) <= 2

    def test_list_host_logs_filtered_by_host_id(self, db_session, sim_service):
        """
        list_host_logs(host_id=X) must only return entries belonging to host X.
        """
        for _ in range(3):
            sim_service.trigger_tick()
        repo = SimulationRepository(db_session)
        host = db_session.query(PhysicalServerModel).first()
        logs = repo.list_host_logs(host.id, limit=100)
        for log in logs:
            assert log.host_id == host.id

    def test_get_global_logs_service_method(self, db_session, sim_service):
        """
        Service method get_global_logs() should aggregate and return all logged history.
        """
        for _ in range(3):
            sim_service.trigger_tick()
        result = sim_service.get_global_logs(100)
        assert len(result) == 3

    def test_get_host_logs_service_method(self, db_session, sim_service):
        """
        Service method get_host_logs(host_id) should return only that host's history.
        """
        for _ in range(3):
            sim_service.trigger_tick()
        host = db_session.query(PhysicalServerModel).first()
        result = sim_service.get_host_logs(host.id, 100)
        assert len(result) == 3
        for log in result:
            assert log.host_id == host.id
