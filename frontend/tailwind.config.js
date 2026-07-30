/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Dark theme premium palette (Azure/Datadog/Grafana inspired)
        background: "#080c14",
        panel: "rgba(16, 22, 35, 0.65)",
        panelBorder: "rgba(255, 255, 255, 0.08)",
        primary: {
          DEFAULT: "#00d2ff",
          dark: "#0099cc",
          light: "#80e5ff",
        },
        secondary: {
          DEFAULT: "#7928ca",
          dark: "#5700b3",
          light: "#b270f2",
        },
        accent: {
          green: "#00e676",  // Idle / Normal
          yellow: "#ffd600", // Active / Busy
          red: "#ff1744",    // Overloaded
          gray: "#757575",   // Sleeping / Off
        },
        cardBg: "rgba(30, 41, 59, 0.4)",
      },
      backdropBlur: {
        xs: "2px",
      },
      boxShadow: {
        glass: "0 8px 32px 0 rgba(0, 0, 0, 0.37)",
        glassInner: "inset 0 1px 1px 0 rgba(255, 255, 255, 0.05)",
      },
    },
  },
  plugins: [],
}
