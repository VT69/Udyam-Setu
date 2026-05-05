import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts';

export default function ShapWaterfall({ data }) {
  if (!data || data.length === 0) return <div className="text-steel-light text-sm italic">No SHAP data available</div>;

  // Format data for Recharts
  // We want to show positive contributions stretching right, negative left
  const chartData = data.map(d => ({
    name: d.feature,
    value: parseFloat(d.contribution.toFixed(4)),
    displayValue: d.value
  }));

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-navy border border-steel-dark p-3 rounded-lg shadow-xl">
          <p className="text-white font-sora font-semibold text-sm mb-1">{data.name}</p>
          <p className="text-steel-light text-xs font-mono mb-2">Feature Value: {data.displayValue}</p>
          <p className={`text-xs font-mono font-medium ${data.value > 0 ? 'text-green-400' : 'text-red-400'}`}>
            SHAP Impact: {data.value > 0 ? '+' : ''}{data.value}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <XAxis type="number" hide />
          <YAxis dataKey="name" type="category" width={150} tick={{ fill: '#778DA9', fontSize: 12, fontFamily: 'IBM Plex Mono' }} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: '#1B263B' }} />
          <ReferenceLine x={0} stroke="#3D5A73" />
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.value > 0 ? '#4ADE80' : '#F87171'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
