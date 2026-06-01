import type { Config } from "tailwindcss";

// UnitedHealthcare / Optum brand palette.
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        uhc: {
          blue: "#002677",        // UHC primary deep blue
          "blue-bright": "#0066B3", // bright accent blue
          "blue-soft": "#E8F0FB",  // light blue surface
        },
        optum: {
          orange: "#FF612B",      // Optum orange
          "orange-dark": "#E0551F",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
      },
      boxShadow: {
        card: "0 8px 30px rgba(0, 38, 119, 0.10)",
      },
    },
  },
  plugins: [],
};

export default config;
