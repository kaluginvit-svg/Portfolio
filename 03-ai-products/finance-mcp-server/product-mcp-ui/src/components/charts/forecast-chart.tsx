"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { LiquidityDay } from "@/types/finance";

export function ForecastChart({ data }: { data: LiquidityDay[] }) {
  const chartData = data.map((d) => ({
    date: d.date.slice(5),
    cash: Math.round(d.running_cash * 100) / 100,
  }));
  if (!chartData.length) return <p className="text-sm text-muted-foreground">No projection points to chart.</p>;
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Line type="monotone" dataKey="cash" stroke="hsl(221, 83%, 40%)" strokeWidth={2} dot={false} name="Running cash" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
