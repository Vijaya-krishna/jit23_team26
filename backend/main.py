import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.utils.config import settings
from backend.database.session import engine, Base, SessionLocal
from backend.database.models.user_model import UserModel
from backend.database.models.simulation_models import PhysicalServerModel, VirtualMachineModel, SimulationStateModel, TaskModel, GlobalTelemetryLogModel, HostTelemetryLogModel
from backend.database.schemas.user_schema import UserCreate
from backend.api.repositories.user_repository import UserRepository
from backend.api.services.auth_service import AuthService
from backend.api.controllers import auth_controller, simulation_controller, power_controller, scheduler_controller, reports_controller

# Configure logger reporting
logger = logging.getLogger("main")
logging.basicConfig(level=logging.INFO)

# Create database tables if they do not exist
# Note: Importing simulation models above ensures SQLAlchemy auto-creates physical_servers and virtual_machines tables
Base.metadata.create_all(bind=engine)

def seed_database(db: Session):
    """
    Seeds a default administrator user and physical servers on startup if no accounts exist.
    """
    # 1. Seed user accounts
    user_repo = UserRepository(db)
    existing_users = user_repo.list_all()
    if not existing_users:
        logger.info("Database is empty. Seeding default administrator account...")
        auth_service = AuthService(user_repo)
        admin_data = UserCreate(
            username=settings.DEFAULT_ADMIN_USERNAME,
            email=settings.DEFAULT_ADMIN_EMAIL,
            role="admin",
            password=settings.DEFAULT_ADMIN_PASSWORD
        )
        auth_service.register_user(admin_data)
        logger.info(f"Admin account created: {settings.DEFAULT_ADMIN_USERNAME} / {settings.DEFAULT_ADMIN_PASSWORD}")

    # 2. Seed physical servers
    existing_servers = db.query(PhysicalServerModel).all()
    if not existing_servers:
        logger.info("Database has no servers. Seeding 5 physical servers...")
        servers = [
            PhysicalServerModel(
                cpu_cores=16, cpu_frequency_ghz=3.2, ram_mb=64000.0, storage_gb=2000.0, bandwidth_mbps=10000.0,
                power_state="ACTIVE", temperature=22.0, cpu_utilization=0.0, ram_utilization=0.0,
                storage_utilization=0.0, bandwidth_utilization=0.0, power_consumption=80.0
            ),
            PhysicalServerModel(
                cpu_cores=32, cpu_frequency_ghz=3.0, ram_mb=128000.0, storage_gb=4000.0, bandwidth_mbps=10000.0,
                power_state="ACTIVE", temperature=22.0, cpu_utilization=0.0, ram_utilization=0.0,
                storage_utilization=0.0, bandwidth_utilization=0.0, power_consumption=80.0
            ),
            PhysicalServerModel(
                cpu_cores=8, cpu_frequency_ghz=3.6, ram_mb=32000.0, storage_gb=1000.0, bandwidth_mbps=10000.0,
                power_state="ACTIVE", temperature=22.0, cpu_utilization=0.0, ram_utilization=0.0,
                storage_utilization=0.0, bandwidth_utilization=0.0, power_consumption=80.0
            ),
            PhysicalServerModel(
                cpu_cores=16, cpu_frequency_ghz=3.2, ram_mb=64000.0, storage_gb=2000.0, bandwidth_mbps=10000.0,
                power_state="ACTIVE", temperature=22.0, cpu_utilization=0.0, ram_utilization=0.0,
                storage_utilization=0.0, bandwidth_utilization=0.0, power_consumption=80.0
            ),
            PhysicalServerModel(
                cpu_cores=32, cpu_frequency_ghz=3.0, ram_mb=128000.0, storage_gb=4000.0, bandwidth_mbps=10000.0,
                power_state="ACTIVE", temperature=22.0, cpu_utilization=0.0, ram_utilization=0.0,
                storage_utilization=0.0, bandwidth_utilization=0.0, power_consumption=80.0
            ),
        ]
        db.add_all(servers)
        db.commit()
        logger.info("Successfully seeded 5 physical hosts.")

    # 3. Seed default simulation state
    existing_state = db.query(SimulationStateModel).filter(SimulationStateModel.id == 1).first()
    if not existing_state:
        logger.info("Seeding default simulation state...")
        state = SimulationStateModel(id=1, tick_counter=0, total_energy_kwh=0.0)
        db.add(state)
        db.commit()
        logger.info("Successfully seeded default simulation state.")


# Run seed database
db = SessionLocal()
try:
    seed_database(db)
finally:
    db.close()

# Initialize FastAPI App
app = FastAPI(
    title="Energy-Aware Resource Allocation Simulator API",
    description="Research-Grade Cloud Simulation Engine Backend API",
    version="1.0.0"
)

# Configure CORS Middleware
# Allows requests from Vite React frontend (usually localhost:5173 or localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_controller.router)
app.include_router(simulation_controller.router)
app.include_router(power_controller.router)
app.include_router(scheduler_controller.router)
app.include_router(reports_controller.router)

@app.get("/")
def read_root():
    """
    Root status endpoint.
    """
    return {
        "status": "online",
        "service": "Energy-Aware Resource Allocation Simulator API",
        "version": "1.0.0"
    }
