import { useState,useEffect } from "react";
import useMetrics from "./hooks/useMetrics";
import NavBar from "./components/NavBar";
import StatCards from "./components/StatCards";
import TimeSeriesChart from "./components/TimeSeriesChart";
import DnsChart from "./components/DnsChart";
import WiFiRadioChart from "./components/WiFiRadioChart";
import DeviceCorrelationChart from "./components/DeviceCorrelationChart";
import RawTable from "./components/RawTable";

export default function App() {
  const { timeseries, summary, latest, loading, error } = useMetrics();
  const [dismissedError, setDismissedError] = useState(false);
  const [darkMode, setDarkMode] = useState(
    localStorage.getItem("theme") === "dark"
  );
 
  useEffect(()=>{
    if(darkMode){
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    }
    else{
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme","light");
    }
  },[darkMode])
  return (
    <>
      <NavBar darkMode = {darkMode} setDarkMode= {setDarkMode} ssid={latest?.wifi_ssid} lastUpdated={latest?.timestamp} />
      <div className="pt-16 min-h-screen dark:bg-zinc-900 bg-slate-200">
        <div className="max-w-7xl mx-auto px-4 py-6">
          {error != null && error !== "" && !dismissedError && (
            <div className="dark:bg-zinc-800 mb-4 flex items-center justify-between gap-4 rounded-lg bg-red-50 border dark:border-zinc-700 border-red-100 px-4 py-3 text-red-700 text-sm">
              <span>{error}</span>
              <button
                type="button"
                onClick={() => setDismissedError(true)}
                className="shrink-0 text-red-500 hover:text-red-700 font-medium"
              >
                Dismiss
              </button>
            </div>
          )}
          {loading ? (
            <div className="flex justify-center items-center py-24">
              <div className="animate-spin rounded-full h-10 w-10 border-2 border-gray-200 border-t-blue-500" />
            </div>
          ) : (
            <>
              <section id="overview" className="mb-8">
                <StatCards summary={summary} />
              </section>
              <section id="charts" className="space-y-6 mb-8">
                <TimeSeriesChart data={timeseries} />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <DnsChart data={timeseries} />
                  <WiFiRadioChart data={timeseries} />
                </div>
                <DeviceCorrelationChart data={timeseries} />
              </section>
              <section id="raw-data" className="mb-8">
                <RawTable/>
              </section>
            </>
          )}
        </div>
      </div>
    </>
  );
}
