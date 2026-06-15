import React, { useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { FiArrowLeft, FiShare2, FiAlertTriangle, FiCheck, FiDownload, FiInfo } from "react-icons/fi";
import toast from "react-hot-toast";
import UrgencyBadge from "@components/common/UrgencyBadge";

import { formatDate, formatConfidence } from "@utils/formatters";
import { submitFeedback, downloadReport } from "@services/api";

const DISEASE_CLASSES = [
  "Normal",
  "Edema",
  "Pneumothorax",
  "Pneumonia-Bacterial",
  "Pneumonia-Viral",
  "COVID-19",
  "Tuberculosis",
  "Emphysema",
];

const Result = () => {
  const { state } = useLocation();
  const navigate = useNavigate();
  const { id } = useParams();

  const prediction = state?.prediction;

  const [showFeedback, setShowFeedback] = useState(false);
  const [selectedClass, setSelectedClass] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [feedbackDone, setFeedbackDone] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [showHeatmap, setShowHeatmap] = useState(true);

  const handleShare = async () => {
    try {
      const url = window.location.href;
      if (navigator.share) {
        await navigator.share({
          title: "Lung Disease Screening Result",
          text: "AI-assisted chest X-ray screening result.",
          url
        });
      } else {
        await navigator.clipboard.writeText(url);
      }
    } catch {
      // ignore share errors
    }
  };

  const handleDownloadPDF = async () => {
    setDownloading(true);
    try {
      const response = await downloadReport(prediction.id);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `LDD_Report_${prediction.id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success("Medical report downloaded successfully.");
    } catch (error) {
      console.error("Download failed", error);
    } finally {
      setDownloading(false);
    }
  };

  const handleFeedbackSubmit = async () => {
    if (!selectedClass) {
      toast.error("Please select the correct disease class.");
      return;
    }
    setSubmitting(true);
    try {
      await submitFeedback(prediction.id, selectedClass);
      toast.success("Thank you! Your feedback has been recorded for model improvement.");
      setFeedbackDone(true);
      setShowFeedback(false);
    } catch {
      toast.error("Failed to submit feedback. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  if (!prediction) {
    return (
      <section className="space-y-4">
        <button
          type="button"
          onClick={() => navigate("/")}
          className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200"
        >
          <FiArrowLeft className="h-4 w-4" />
          Back to upload
        </button>
        <div className="rounded-lg border border-slate-700 bg-surface p-4 text-sm text-slate-200">
          Prediction details are not available in this session. Please upload an
          image again to view a detailed result.
        </div>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <button
        type="button"
        onClick={() => navigate(-1)}
        className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200"
      >
        <FiArrowLeft className="h-4 w-4" />
        Back
      </button>

      <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-50">
            Screening Result
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Prediction ID: {prediction.id} • {formatDate(prediction.created_at)}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <UrgencyBadge
            level={prediction.urgency_level}
            icon={prediction.urgency_icon}
            label={prediction.urgency_level.replace("_", " ")}
          />
          <button
            type="button"
            onClick={handleDownloadPDF}
            disabled={downloading}
            className="inline-flex items-center gap-1 rounded-full bg-blue-600 px-3 py-1 text-xs font-medium text-white hover:bg-blue-500 shadow-lg transition-all active:scale-95 disabled:opacity-50"
          >
            <FiDownload className="h-4 w-4" />
            {downloading ? "Generating..." : "Download Report"}
          </button>
          <button
            type="button"
            onClick={handleShare}
            className="inline-flex items-center gap-1 rounded-full border border-slate-600 px-3 py-1 text-xs text-slate-200 hover:bg-slate-800"
          >
            <FiShare2 className="h-4 w-4" />
            Share
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1 space-y-4">
          <div className="bg-surface rounded-xl border border-slate-800 overflow-hidden shadow-card relative group">
            {showHeatmap && prediction.heatmap_image_url ? (
              <img
                src={prediction.heatmap_image_url}
                alt="AI Heatmap overlay"
                className="w-full h-64 object-contain bg-black"
              />
            ) : prediction.image_url ? (
              <img
                src={prediction.image_url}
                alt="Chest X-ray analyzed"
                className="w-full h-64 object-contain bg-black"
              />
            ) : null}

            {prediction.heatmap_image_url && (
              <button
                onClick={() => setShowHeatmap(!showHeatmap)}
                className="absolute bottom-3 right-3 bg-black/60 backdrop-blur-md border border-slate-700 rounded-lg px-2 py-1 text-[10px] font-medium text-slate-200 hover:bg-blue-600 transition-all flex items-center gap-1"
              >
                {showHeatmap ? "View Original" : "View AI Heatmap"}
              </button>
            )}
          </div>

          {prediction.heatmap_image_url && showHeatmap && (
            <div className="p-3 rounded-lg bg-primary-950/20 border border-primary-900/40 text-[10px] text-primary-300 flex gap-2">
              <FiInfo className="shrink-0 h-4 w-4" />
              <p>
                <span className="font-bold">AI AI Interpretability (Grad-CAM):</span> The highlighted areas show where the AI focused its attention to make this diagnosis. Warmer colors (red/orange) indicate higher relevance.
              </p>
            </div>
          )}
        </div>
        <div className="md:col-span-2 space-y-4">
          <div className="bg-surface rounded-lg border border-slate-800 p-4 space-y-2">
            <h2 className="text-sm font-semibold text-slate-100">
              AI Assessment
            </h2>
            <p className="text-base font-semibold text-slate-50">
              {prediction.predicted_class}
            </p>
            <div className="mt-2">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>Model confidence</span>
                <span>{formatConfidence(prediction.confidence_score)}</span>
              </div>
              <div className="mt-1 h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-blue-500 shadow-sm shadow-blue-500/50"
                  style={{ width: `${prediction.confidence_percentage.toFixed(2)}%` }}
                />
              </div>
            </div>
          </div>

          {/* ── Feedback / Correction Section ── */}
          {!feedbackDone ? (
            <div className="bg-surface rounded-lg border border-slate-800 p-4">
              {!showFeedback ? (
                <button
                  type="button"
                  onClick={() => setShowFeedback(true)}
                  className="inline-flex items-center gap-2 rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-2 text-xs font-medium text-amber-300 hover:bg-amber-500/20 transition-colors"
                >
                  <FiAlertTriangle className="h-4 w-4" />
                  Report Incorrect Prediction
                </button>
              ) : (
                <div className="space-y-3">
                  <p className="text-xs text-slate-300">
                    What is the correct diagnosis for this X-ray?
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {DISEASE_CLASSES.map((cls) => (
                      <button
                        key={cls}
                        type="button"
                        onClick={() => setSelectedClass(cls)}
                        className={`rounded-full px-3 py-1.5 text-xs font-medium border transition-colors ${selectedClass === cls
                          ? "border-blue-500 bg-blue-500/20 text-blue-300"
                          : "border-slate-600 text-slate-300 hover:bg-slate-700"
                          }`}
                      >
                        {cls}
                      </button>
                    ))}
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={handleFeedbackSubmit}
                      disabled={submitting || !selectedClass}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium text-white hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {submitting ? "Submitting…" : "Submit Correction"}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setShowFeedback(false);
                        setSelectedClass("");
                      }}
                      className="rounded-lg px-3 py-2 text-xs text-slate-400 hover:text-slate-200"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="rounded-lg border border-green-500/40 bg-green-500/10 p-3 text-xs text-green-300 flex items-center gap-2">
              <FiCheck className="h-4 w-4" />
              Feedback recorded. This image will be used to improve the model. Thank you!
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="bg-surface rounded-lg border border-slate-800 p-4">
              <h3 className="font-semibold text-slate-100">
                Immediate actions
              </h3>
              <ul className="mt-2 list-disc list-inside space-y-1 text-slate-300">
                {prediction.immediate_actions?.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
            <div className="bg-surface rounded-lg border border-slate-800 p-4">
              <h3 className="font-semibold text-slate-100">
                Medical recommendations
              </h3>
              <ul className="mt-2 list-disc list-inside space-y-1 text-slate-300">
                {prediction.medical_recommendations?.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="bg-surface rounded-lg border border-slate-800 p-4">
              <h3 className="font-semibold text-slate-100">
                Lifestyle recommendations
              </h3>
              <ul className="mt-2 list-disc list-inside space-y-1 text-slate-300">
                {prediction.lifestyle_recommendations?.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
            <div className="bg-surface rounded-lg border border-slate-800 p-4">
              <h3 className="font-semibold text-slate-100">Follow-up</h3>
              <p className="mt-2 text-slate-300">{prediction.follow_up}</p>
            </div>
          </div>

          {/* ── AI Symptom Analysis Section ── */}
          {prediction.symptoms && (
            <div className="bg-gradient-to-br from-teal-900/40 to-cyan-900/30 rounded-lg border border-teal-500/40 p-4 space-y-3">
              <h3 className="text-sm font-semibold text-teal-200 flex items-center gap-2">
                🧬 AI Symptom Analysis (AI-Powered)
              </h3>
              <p className="text-xs text-slate-300">
                <span className="font-medium text-slate-200">Reported symptoms:</span>{" "}
                {prediction.symptoms}
              </p>
              {prediction.immediate_actions?.filter(a => a.startsWith("[AI Suggestion]")).length > 0 && (
                <div className="space-y-2 mt-2">
                  <p className="text-xs font-medium text-teal-300">AI Medical Analysis:</p>
                  <div className="bg-black/20 rounded-lg p-3 space-y-2">
                    {prediction.immediate_actions
                      .filter(a => a.startsWith("[AI Suggestion]"))
                      .map((item) => item.replace("[AI Suggestion]: ", ""))
                      .join("")
                      .split("\n")
                      .filter(p => p.trim())
                      .map((paragraph, idx) => (
                        <p key={idx} className="text-xs text-teal-100 leading-relaxed">
                          {paragraph.trim()}
                        </p>
                      ))}
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="rounded-lg border border-yellow-500/60 bg-yellow-500/5 p-3 text-xs text-yellow-100">
            {prediction.disclaimer}
          </div>
        </div>
      </div>


    </section>
  );
};

export default Result;
