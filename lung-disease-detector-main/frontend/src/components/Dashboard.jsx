import React, { useEffect, useState } from "react";
import {
    PieChart,
    Pie,
    Cell,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    LineChart,
    Line,
} from "recharts";
import { getDashboardStats, retrainModel } from "../services/api";
import { FiActivity, FiAlertTriangle, FiCheckCircle, FiFileText } from "react-icons/fi";
import { useAuth } from "../context/AuthContext";
import { toast } from "react-hot-toast";

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884d8"];

const AdminRetrainButton = () => {
    const { user } = useAuth();
    const [loading, setLoading] = useState(false);

    // Only show for superusers
    if (!user?.is_superuser) return null;

    const handleRetrain = async () => {
        if (!window.confirm("Are you sure you want to trigger model retraining? This may take a while.")) return;

        setLoading(true);
        try {
            const res = await retrainModel();
            toast.success(res.message);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <button
            onClick={handleRetrain}
            disabled={loading}
            className={`
                flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all
                ${loading
                    ? "bg-slate-700 text-slate-400 cursor-not-allowed"
                    : "bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg shadow-indigo-500/20 active:scale-95"}
            `}
        >
            {loading ? (
                <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Starting Task...</span>
                </>
            ) : (
                <>
                    <FiActivity />
                    <span>Retrain Model</span>
                </>
            )}
        </button>
    );
};

const Dashboard = () => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const data = await getDashboardStats();
                setStats(data);
            } catch (err) {
                console.error("Failed to fetch stats:", err);
                setError("Failed to load dashboard statistics.");
            } finally {
                setLoading(false);
            }
        };

        fetchStats();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="text-center p-8 text-red-400 bg-surface rounded-lg border border-red-900/30">
                <FiAlertTriangle className="mx-auto h-12 w-12 mb-4" />
                <p>{error}</p>
            </div>
        );
    }

    if (!stats) return null;

    return (
        <div className="space-y-8 animate-fade-in">
            <header className="mb-8 flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold text-slate-50 mb-2">Analytics Dashboard</h1>
                    <p className="text-slate-400">Overview of system performance and disease statistics.</p>
                </div>
                <AdminRetrainButton />
            </header>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    title="Total Scans"
                    value={stats.total_scans}
                    icon={<FiFileText className="h-6 w-6 text-blue-400" />}
                    color="bg-blue-500/10 border-blue-500/20"
                />
                <StatCard
                    title="Critical Cases"
                    value={stats.critical_cases}
                    icon={<FiAlertTriangle className="h-6 w-6 text-red-400" />}
                    color="bg-red-500/10 border-red-500/20"
                />
                <StatCard
                    title="Reported Issues"
                    value={stats.reported_errors}
                    icon={<FiActivity className="h-6 w-6 text-yellow-400" />}
                    color="bg-yellow-500/10 border-yellow-500/20"
                />
                <StatCard
                    title="System Status"
                    value="Healthy"
                    icon={<FiCheckCircle className="h-6 w-6 text-green-400" />}
                    color="bg-green-500/10 border-green-500/20"
                />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Disease Distribution */}
                <div className="bg-surface rounded-xl p-6 border border-slate-700/50 shadow-sm">
                    <h3 className="text-lg font-semibold text-slate-100 mb-6">Disease Distribution</h3>
                    <div style={{ width: "100%", height: 320 }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={stats.disease_distribution.filter((d) => d.predicted_class !== "Unknown")}
                                    cx="50%"
                                    cy="45%"
                                    innerRadius={60}
                                    outerRadius={80}
                                    fill="#8884d8"
                                    paddingAngle={5}
                                    dataKey="count"
                                    nameKey="predicted_class"
                                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                >
                                    {stats.disease_distribution
                                        .filter((d) => d.predicted_class !== "Unknown")
                                        .map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{ backgroundColor: "#1e293b", borderColor: "#334155", color: "#f8fafc" }}
                                    itemStyle={{ color: "#f8fafc" }}
                                />
                                <Legend layout="horizontal" verticalAlign="bottom" align="center" />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Recent Activity */}
                <div className="bg-surface rounded-xl p-6 border border-slate-700/50 shadow-sm">
                    <h3 className="text-lg font-semibold text-slate-100 mb-6">Last 7 Days Activity</h3>
                    <div style={{ width: "100%", height: 320 }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={stats.daily_scans} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickFormatter={(date) => new Date(date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })} />
                                <YAxis stroke="#94a3b8" fontSize={12} allowDecimals={false} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: "#1e293b", borderColor: "#334155", color: "#f8fafc" }}
                                    cursor={{ fill: "#334155", opacity: 0.4 }}
                                />
                                <Bar dataKey="count" name="Scans" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </div>
    );
};

// Sub-component for KPI cards
const StatCard = ({ title, value, icon, color }) => (
    <div className={`rounded-xl p-5 border ${color} transition-all hover:scale-[1.02]`}>
        <div className="flex items-center justify-between mb-4">
            <div className="p-2 rounded-lg bg-surface/50 backdrop-blur-sm">{icon}</div>
        </div>
        <div className="flex flex-col">
            <span className="text-sm font-medium text-slate-400">{title}</span>
            <span className="text-2xl font-bold text-slate-100 mt-1">{value}</span>
        </div>
    </div>
);

export default Dashboard;
