import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FiSearch } from "react-icons/fi";
import LoadingSpinner from "@components/common/LoadingSpinner";
import UrgencyBadge from "@components/common/UrgencyBadge";
import { getPredictionHistory } from "@services/api";
import { formatDate, truncateText } from "@utils/formatters";
import PatientProgressChart from "./PatientProgressChart";
import { useAuth } from "../context/AuthContext";

const PER_PAGE = 10;

const History = () => {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [page, setPage] = useState(1);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [diseaseFilter, setDiseaseFilter] = useState("");
  const [search, setSearch] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const params = { page };
        if (diseaseFilter) params.predicted_class = diseaseFilter;
        if (search) params.search = search;
        const { data } = await getPredictionHistory(params);
        setItems(data.results || []);
        setCount(data.count || 0);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [page, diseaseFilter, search]);

  const totalPages = Math.max(1, Math.ceil(count / PER_PAGE));

  return (
    <section className="space-y-6">
      <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-50">
            Prediction History
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            View recent AI-assisted screenings. Only anonymized images should be
            used in clinical environments.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <FiSearch className="absolute left-2 top-2.5 h-3.5 w-3.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search by ID or disease"
              className="pl-7 pr-3 py-1.5 rounded-md bg-slate-900 border border-slate-700 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus-visible:ring-1 focus-visible:ring-blue-500"
              value={search}
              onChange={(e) => {
                setPage(1);
                setSearch(e.target.value);
              }}
            />
          </div>
          <select
            className="text-xs bg-slate-900 border border-slate-700 rounded-md px-2 py-1 text-slate-100 focus:outline-none focus-visible:ring-1 focus-visible:ring-blue-500"
            value={diseaseFilter}
            onChange={(e) => {
              setPage(1);
              setDiseaseFilter(e.target.value);
            }}
          >
            <option value="">All diseases</option>
            <option value="Atelectasis">Atelectasis</option>
            <option value="Cardiomegaly">Cardiomegaly</option>
            <option value="Consolidation">Consolidation</option>
            <option value="Edema">Edema</option>
            <option value="Effusion">Effusion</option>
            <option value="Emphysema">Emphysema</option>
            <option value="Fibrosis">Fibrosis</option>
            <option value="Hernia">Hernia</option>
            <option value="Infiltration">Infiltration</option>
            <option value="Mass">Mass</option>
            <option value="Nodule">Nodule</option>
            <option value="Pleural_Thickening">Pleural_Thickening</option>
            <option value="Pneumonia">Pneumonia</option>
            <option value="Pneumothorax">Pneumothorax</option>
            <option value="COVID-19">COVID-19</option>
            <option value="Tuberculosis">Tuberculosis</option>
            <option value="Normal">Normal</option>
          </select>
        </div>
      </header>

      {/* Render the chart here */}
      {!loading && items.length > 0 && (
        <PatientProgressChart history={items} diseaseFilter={diseaseFilter} search={search} user={user} />
      )}

      <div className="bg-surface rounded-xl border border-slate-800 p-4">
        {loading ? (
          <div className="flex justify-center py-6">
            <LoadingSpinner label="Loading history..." />
          </div>
        ) : items.length === 0 ? (
          <p className="text-sm text-slate-400">
            No predictions found yet. Upload a chest X-ray to get started.
          </p>
        ) : (
          <ul className="divide-y divide-slate-800">
            {items.map((item) => (
              <li
                key={item.id}
                className="py-3 flex items-center gap-3 cursor-pointer hover:bg-slate-900 rounded-md px-2"
                onClick={() =>
                  navigate(`/result/${item.id}`, {
                    state: { prediction: item }
                  })
                }
              >
                {item.image_url && (
                  <img
                    src={item.image_url}
                    alt="X-ray thumbnail"
                    loading="lazy"
                    className="h-14 w-14 rounded-md object-cover bg-black flex-shrink-0"
                  />
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-xs font-semibold text-slate-100">
                      {item.predicted_class}
                    </p>
                    <UrgencyBadge
                      level={item.urgency_level}
                      icon={item.urgency_icon}
                      label={item.urgency_level.replace("_", " ")}
                    />
                  </div>
                  <p className="mt-0.5 text-[11px] text-slate-400">
                    ID: {item.id} • {formatDate(item.created_at)}
                  </p>
                  <p className="mt-0.5 text-[11px] text-slate-500">
                    {truncateText(item.follow_up, 90)}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        )}

        {count > 0 && (
          <div className="flex items-center justify-between mt-4 text-[11px] text-slate-400">
            <span>
              Page {page} of {totalPages}
            </span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-2 py-1 rounded-md border border-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                type="button"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className="px-2 py-1 rounded-md border border-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </section>
  );
};

export default History;

