import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Cloud, Sun, CloudRain, CloudDrizzle, CloudSun, Wind, Droplets,
  Thermometer, CloudLightning, RotateCcw, CloudSnow,
} from "lucide-react";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

/* ------------------------------------------------------------------ */
/*  TYPES                                                              */
/* ------------------------------------------------------------------ */

interface DayForecast {
  day: string;
  date: string;
  iconKey: string;
  temp: number;
  condition: string;
  humidity: number;
  rainfallProb: number;
  rainfallAmount: number;
  windSpeed: number;
  predicted: boolean;
}

interface HourData {
  hour: string;
  Temperature: number;
  Humidity: number;
  WindSpeed: number;
  Rainfall: number;
}

/* ------------------------------------------------------------------ */
/*  ICON MAP                                                           */
/* ------------------------------------------------------------------ */

const iconMap: Record<string, React.ReactNode> = {
  sun: <Sun className="w-8 h-8" />,
  cloudSun: <CloudSun className="w-8 h-8" />,
  cloud: <Cloud className="w-8 h-8" />,
  drizzle: <CloudDrizzle className="w-8 h-8" />,
  rain: <CloudRain className="w-8 h-8" />,
  thunder: <CloudLightning className="w-8 h-8" />,
  snow: <CloudSnow className="w-8 h-8" />,
};

/* ------------------------------------------------------------------ */
/*  SEED-BASED PSEUDO-RANDOM GENERATOR                                 */
/* ------------------------------------------------------------------ */

function seededRandom(seed: number) {
  let s = seed;
  return () => {
    s = (s * 16807 + 0) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

/* ------------------------------------------------------------------ */
/*  DATA GENERATORS                                                    */
/* ------------------------------------------------------------------ */

const conditions: { key: string; icon: string; minTemp: number; maxTemp: number; humRange: [number, number]; rainProb: number }[] = [
  { key: "Sunny", icon: "sun", minTemp: 30, maxTemp: 36, humRange: [40, 60], rainProb: 5 },
  { key: "Partly Cloudy", icon: "cloudSun", minTemp: 27, maxTemp: 33, humRange: [50, 70], rainProb: 20 },
  { key: "Cloudy", icon: "cloud", minTemp: 24, maxTemp: 30, humRange: [60, 80], rainProb: 40 },
  { key: "Light Rain", icon: "drizzle", minTemp: 22, maxTemp: 28, humRange: [70, 88], rainProb: 65 },
  { key: "Rainy", icon: "rain", minTemp: 20, maxTemp: 26, humRange: [78, 92], rainProb: 80 },
  { key: "Thunderstorm", icon: "thunder", minTemp: 19, maxTemp: 25, humRange: [85, 95], rainProb: 90 },
];

const dayNames = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

function getWeeksInMonth(year: number, month: number) {
  const first = new Date(year, month, 1);
  const last = new Date(year, month + 1, 0);
  const totalDays = last.getDate();
  // Start from the Monday of the week containing the 1st
  const firstDayOfWeek = (first.getDay() + 6) % 7; // 0=Mon
  const weeks: { label: string; startDate: Date }[] = [];
  let d = new Date(year, month, 1 - firstDayOfWeek);
  for (let w = 0; w < 5; w++) {
    const wStart = new Date(d);
    if (wStart.getMonth() > month && wStart.getFullYear() >= year && w > 0) break;
    if (w > 0 && wStart.getDate() > totalDays && wStart.getMonth() === month) break;
    weeks.push({ label: `Week ${w + 1}`, startDate: new Date(wStart) });
    d.setDate(d.getDate() + 7);
  }
  return weeks;
}

function generateWeekForecast(startDate: Date, isPredicted: boolean): DayForecast[] {
  const seed = startDate.getFullYear() * 10000 + startDate.getMonth() * 100 + startDate.getDate();
  const rand = seededRandom(seed);
  const result: DayForecast[] = [];
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  for (let i = 0; i < 7; i++) {
    const d = new Date(startDate);
    d.setDate(d.getDate() + i);
    const ci = Math.floor(rand() * conditions.length);
    const c = conditions[ci];
    const temp = Math.round(c.minTemp + rand() * (c.maxTemp - c.minTemp));
    const hum = Math.round(c.humRange[0] + rand() * (c.humRange[1] - c.humRange[0]));
    const rainProb = Math.round(c.rainProb + (rand() - 0.5) * 20);
    const rainAmt = rainProb > 40 ? Math.round(rand() * 40) : Math.round(rand() * 3);
    const ws = Math.round(8 + rand() * 25);
    const dayIsFuture = d > today;

    result.push({
      day: dayNames[i],
      date: `${monthNames[d.getMonth()].slice(0, 3)} ${d.getDate()}`,
      iconKey: c.icon,
      temp,
      condition: c.key,
      humidity: hum,
      rainfallProb: Math.max(0, Math.min(100, rainProb)),
      rainfallAmount: rainAmt,
      windSpeed: ws,
      predicted: isPredicted || dayIsFuture,
    });
  }
  return result;
}

function generateHourlyData(day: DayForecast): HourData[] {
  const seed = day.temp * 100 + day.humidity + day.windSpeed;
  const rand = seededRandom(seed);
  const hours: HourData[] = [];
  for (let h = 0; h < 24; h++) {
    const nightFactor = h < 6 || h > 20 ? -4 : h < 10 ? (h - 6) * 1.2 : h < 16 ? 2 : -(h - 16) * 0.8;
    hours.push({
      hour: `${String(h).padStart(2, "0")}:00`,
      Temperature: Math.round(day.temp + nightFactor + (rand() - 0.5) * 3),
      Humidity: Math.round(day.humidity + (rand() - 0.5) * 15),
      WindSpeed: Math.round(day.windSpeed + (rand() - 0.5) * 10),
      Rainfall: day.rainfallProb > 40 ? Math.round(rand() * day.rainfallAmount / 6 * 10) / 10 : 0,
    });
  }
  return hours;
}

/* ------------------------------------------------------------------ */
/*  COMPONENT                                                          */
/* ------------------------------------------------------------------ */

const WeatherForecast = () => {
  const now = new Date();
  const [selectedMonth, setSelectedMonth] = useState(now.getMonth());
  const [selectedYear] = useState(now.getFullYear());

  const weeks = useMemo(() => getWeeksInMonth(selectedYear, selectedMonth), [selectedYear, selectedMonth]);

  // Determine default week (current week or first)
  const defaultWeekIdx = useMemo(() => {
    const today = new Date();
    for (let i = 0; i < weeks.length; i++) {
      const wEnd = new Date(weeks[i].startDate);
      wEnd.setDate(wEnd.getDate() + 6);
      if (today >= weeks[i].startDate && today <= wEnd) return i;
    }
    return 0;
  }, [weeks]);

  const [selectedWeekIdx, setSelectedWeekIdx] = useState(defaultWeekIdx);
  const [selectedDay, setSelectedDay] = useState<number | null>(null);

  // Keep week idx in bounds when month changes
  const weekIdx = Math.min(selectedWeekIdx, weeks.length - 1);
  const currentWeek = weeks[weekIdx];

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const weekEnd = new Date(currentWeek.startDate);
  weekEnd.setDate(weekEnd.getDate() + 6);
  const isPredicted = currentWeek.startDate > today;

  const forecastData = useMemo(
    () => generateWeekForecast(currentWeek.startDate, isPredicted),
    [currentWeek.startDate, isPredicted]
  );

  const selectedDayData = selectedDay !== null ? forecastData[selectedDay] : null;
  const hourlyData = selectedDayData ? generateHourlyData(selectedDayData) : null;

  const weeklyChartData = forecastData.map((d) => ({
    name: d.day,
    Temperature: d.temp,
    Humidity: d.humidity,
    WindSpeed: d.windSpeed,
    Rainfall: d.rainfallAmount,
  }));

  const weeklyTotal = forecastData.reduce((sum, d) => sum + d.rainfallAmount, 0);

  const chartData = hourlyData ?? weeklyChartData;
  const xKey = hourlyData ? "hour" : "name";
  const viewMode = hourlyData ? "hourly" : "weekly";

  const handleReset = () => {
    setSelectedDay(null);
  };

  const handleMonthChange = (v: string) => {
    setSelectedMonth(Number(v));
    setSelectedWeekIdx(0);
    setSelectedDay(null);
  };

  const handleWeekChange = (v: string) => {
    setSelectedWeekIdx(Number(v));
    setSelectedDay(null);
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-heading font-bold text-foreground">🌦️ Weather Forecast</h1>
        <p className="text-muted-foreground mt-1">7-day AI-powered weather prediction</p>
      </div>

      {/* Controls Row */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <Select value={String(selectedMonth)} onValueChange={handleMonthChange}>
          <SelectTrigger className="w-[160px] bg-card border-border">
            <SelectValue placeholder="Month" />
          </SelectTrigger>
          <SelectContent>
            {monthNames.map((m, i) => (
              <SelectItem key={i} value={String(i)}>{m}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={String(weekIdx)} onValueChange={handleWeekChange}>
          <SelectTrigger className="w-[140px] bg-card border-border">
            <SelectValue placeholder="Week" />
          </SelectTrigger>
          <SelectContent>
            {weeks.map((w, i) => (
              <SelectItem key={i} value={String(i)}>{w.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        {selectedDay !== null && (
          <Button variant="outline" size="sm" onClick={handleReset} className="gap-1.5">
            <RotateCcw className="w-3.5 h-3.5" />
            Reset to Weekly
          </Button>
        )}

        {isPredicted && (
          <Badge variant="secondary" className="ml-auto text-xs bg-secondary/20 text-secondary border-secondary/30">
            Predicted Data
          </Badge>
        )}

        {viewMode === "hourly" && selectedDayData && (
          <Badge variant="outline" className="text-xs">
            Viewing: {selectedDayData.day}, {selectedDayData.date} (Hourly)
          </Badge>
        )}
      </div>

      {/* Weekly Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3 mb-8">
        {forecastData.map((day, i) => (
          <motion.button
            key={`${weekIdx}-${day.day}`}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => setSelectedDay(i)}
            className={`relative bg-card rounded-2xl border-2 p-4 text-center transition-all duration-200 cursor-pointer card-shadow ${
              selectedDay === i
                ? "border-primary bg-leaf-light"
                : "border-border hover:border-primary/30"
            }`}
          >
            {day.predicted && (
              <span className="absolute top-1.5 right-1.5 text-[8px] font-medium text-secondary bg-secondary/15 rounded px-1">
                Predicted
              </span>
            )}
            <p className="text-xs font-medium text-muted-foreground mb-1">{day.day}</p>
            <p className="text-[10px] text-muted-foreground/60">{day.date}</p>
            <div className={`my-3 flex justify-center ${selectedDay === i ? "text-primary" : "text-muted-foreground"}`}>
              {iconMap[day.iconKey]}
            </div>
            <p className="text-xl font-heading font-bold text-foreground">{day.temp}°C</p>
            <p className="text-[10px] text-muted-foreground mt-1 truncate">{day.condition}</p>
            <div className="mt-2 space-y-1">
              <p className="text-[10px] text-humidity flex items-center justify-center gap-1">
                <Droplets className="w-3 h-3" /> {day.humidity}%
              </p>
              <p className="text-[10px] text-rain flex items-center justify-center gap-1">
                <CloudRain className="w-3 h-3" /> {day.rainfallProb}%
              </p>
            </div>
          </motion.button>
        ))}
      </div>

      {/* Detailed Prediction */}
      <AnimatePresence mode="wait">
        {selectedDay !== null && selectedDayData && (
          <motion.div
            key={`${weekIdx}-${selectedDay}`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.25 }}
            className="bg-card rounded-2xl border border-border p-6 card-shadow mb-8"
          >
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-heading font-bold text-foreground">
                📊 Detailed Prediction — {selectedDayData.day}, {selectedDayData.date}
              </h2>
              {selectedDayData.predicted && (
                <Badge variant="secondary" className="text-[10px] bg-secondary/15 text-secondary border-secondary/30">
                  AI Predicted
                </Badge>
              )}
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <DetailCard icon={<Thermometer className="w-5 h-5 text-temp" />} label="Temperature" value={`${selectedDayData.temp}°C`} predicted={selectedDayData.predicted} />
              <DetailCard icon={<Droplets className="w-5 h-5 text-humidity" />} label="Humidity" value={`${selectedDayData.humidity}%`} predicted={selectedDayData.predicted} />
              <DetailCard icon={<Wind className="w-5 h-5 text-wind" />} label="Wind Speed" value={`${selectedDayData.windSpeed} km/h`} predicted={selectedDayData.predicted} />
              <DetailCard icon={<CloudRain className="w-5 h-5 text-rain" />} label="Rainfall Prob." value={`${selectedDayData.rainfallProb}%`} predicted={selectedDayData.predicted} />
              <DetailCard icon={<CloudDrizzle className="w-5 h-5 text-sky" />} label="Rainfall Amount" value={`${selectedDayData.rainfallAmount} mm`} predicted={selectedDayData.predicted} />
              <DetailCard icon={<Cloud className="w-5 h-5 text-muted-foreground" />} label="Condition" value={selectedDayData.condition} predicted={selectedDayData.predicted} />
            </div>
            <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
              <CloudRain className="w-4 h-4 text-rain" />
              Weekly Total Rainfall: <span className="font-bold text-foreground">{weeklyTotal} mm</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-card rounded-2xl border border-border p-6 card-shadow">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-heading font-bold text-foreground">
              Temperature & Humidity {viewMode === "hourly" ? "(Hourly)" : "Trend"}
            </h3>
            {viewMode === "hourly" && (
              <Badge variant="outline" className="text-[10px]">Hourly</Badge>
            )}
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey={xKey} stroke="hsl(var(--muted-foreground))" fontSize={11} interval={viewMode === "hourly" ? 2 : 0} />
              <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid hsl(var(--border))", fontSize: 12 }} />
              <Legend />
              <Line
                type="monotone"
                dataKey="Temperature"
                stroke="hsl(var(--temp))"
                strokeWidth={2.5}
                strokeDasharray={isPredicted ? "6 3" : undefined}
                dot={{ r: viewMode === "hourly" ? 2 : 4 }}
              />
              <Line
                type="monotone"
                dataKey="Humidity"
                stroke="hsl(var(--humidity))"
                strokeWidth={2.5}
                strokeDasharray={isPredicted ? "6 3" : undefined}
                dot={{ r: viewMode === "hourly" ? 2 : 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-card rounded-2xl border border-border p-6 card-shadow">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-heading font-bold text-foreground">
              Wind Speed {viewMode === "hourly" ? "(Hourly)" : "Trend"}
            </h3>
            {viewMode === "hourly" && (
              <Badge variant="outline" className="text-[10px]">Hourly</Badge>
            )}
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey={xKey} stroke="hsl(var(--muted-foreground))" fontSize={11} interval={viewMode === "hourly" ? 2 : 0} />
              <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid hsl(var(--border))", fontSize: 12 }} />
              <Legend />
              <Line
                type="monotone"
                dataKey="WindSpeed"
                stroke="hsl(var(--wind))"
                strokeWidth={2.5}
                strokeDasharray={isPredicted ? "6 3" : undefined}
                dot={{ r: viewMode === "hourly" ? 2 : 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-card rounded-2xl border border-border p-6 card-shadow lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-heading font-bold text-foreground">
              Rainfall (mm) {viewMode === "hourly" ? "— Hourly" : ""}
            </h3>
            {viewMode === "hourly" && (
              <Badge variant="outline" className="text-[10px]">Hourly</Badge>
            )}
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey={xKey} stroke="hsl(var(--muted-foreground))" fontSize={11} interval={viewMode === "hourly" ? 2 : 0} />
              <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid hsl(var(--border))", fontSize: 12 }} />
              <Legend />
              <Bar dataKey="Rainfall" fill="hsl(var(--primary))" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/*  DETAIL CARD                                                        */
/* ------------------------------------------------------------------ */

const DetailCard = ({
  icon, label, value, predicted,
}: {
  icon: React.ReactNode; label: string; value: string; predicted?: boolean;
}) => (
  <div className={`bg-muted rounded-xl p-4 text-center ${predicted ? "border border-dashed border-secondary/40" : ""}`}>
    <div className="flex justify-center mb-2">{icon}</div>
    <p className="text-[10px] text-muted-foreground mb-1">{label}</p>
    <p className="text-sm font-heading font-bold text-foreground">{value}</p>
    {predicted && (
      <p className="text-[8px] text-secondary mt-1 font-medium">Predicted</p>
    )}
  </div>
);

export default WeatherForecast;
