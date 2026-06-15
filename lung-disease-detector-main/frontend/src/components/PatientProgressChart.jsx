import React, { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

const PatientProgressChart = ({ history, diseaseFilter, search, user }) => {
  const isDoctor = user?.is_superuser || user?.role === 'DOCTOR';

  if (isDoctor && (!search || search.trim() === "")) {
    return (
      <div className="bg-surface border border-slate-800 rounded-xl p-6 text-center text-sm text-slate-400 mb-6">
        <p>Type a Patient Name or ID in the search bar above to generate their progression chart.</p>
      </div>
    );
  }

  const chartData = useMemo(() => {
    if (!history || history.length === 0) return [];
    
    // Default to the first (most recent) prediction's class if no filter
    const targetDisease = diseaseFilter || history[0]?.predicted_class;
    if (!targetDisease) return [];

    // We only graph if we have a match on the search string for either patient name or id (if doctor)
    return history
      .filter((item) => {
        const matchesDisease = item.predicted_class === targetDisease;
        if (!isDoctor) return matchesDisease; // Patients see all their own data without a search query

        const searchLower = search.toLowerCase();
        const matchesName = item.patient_name?.toLowerCase().includes(searchLower);
        const matchesId = item.id.toString().includes(searchLower);
        return matchesDisease && (matchesName || matchesId);
      })
      .map((item) => {
        const d = new Date(item.created_at);
        return {
          ...item,
          timestamp: d.getTime(),
          displayDate: d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
          probability: Math.round(item.confidence_percentage)
        };
      })
      .sort((a, b) => a.timestamp - b.timestamp); // Sort ascending (oldest to newest)
  }, [history, diseaseFilter]);

  if (chartData.length < 2) {
    return (
      <div className="bg-surface border border-slate-800 rounded-xl p-6 text-center text-sm text-slate-400 mb-6">
        <p>Not enough data points to plot a progression chart.</p>
        <p className="text-xs mt-1">Upload at least two X-rays with the same predicted disease to see the timeline.</p>
      </div>
    );
  }

  const targetDisease = diseaseFilter || history[0]?.predicted_class;

  return (
    <div className="bg-surface border border-slate-800 rounded-xl p-4 mb-6 shadow-card">
      <div className="mb-4 text-center">
        <h3 className="text-sm font-semibold text-slate-200">
          Progression Timeline: <span className="text-primary-400">{targetDisease}</span>
        </h3>
        <p className="text-xs text-slate-400">Probability confidence over time</p>
      </div>
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis 
              dataKey="displayDate" 
              stroke="#94a3b8" 
              fontSize={11}
              tickMargin={10}
            />
            <YAxis 
              stroke="#94a3b8" 
              fontSize={11}
              domain={[0, 100]}
              tickFormatter={(val) => `${val}%`}
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
              itemStyle={{ color: '#38bdf8', fontWeight: 'bold' }}
              labelStyle={{ color: '#cbd5e1', marginBottom: '4px' }}
              formatter={(value) => [`${value}%`, 'Probability']}
            />
            <Line 
              type="monotone" 
              dataKey="probability" 
              stroke="#38bdf8" 
              strokeWidth={3}
              activeDot={{ r: 6, fill: '#0ea5e9' }} 
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default PatientProgressChart;
