import React from "react";
import PropTypes from "prop-types";
import { generatePredictionPdf } from "@services/pdfGenerator";
import { formatDate, formatConfidence } from "@utils/formatters";
import UrgencyBadge from "@components/common/UrgencyBadge";

const ReportGenerator = ({ prediction }) => {
  const handleDownload = async () => {
    try {
      await generatePredictionPdf("prediction-report");
    } catch (err) {
      console.error(err);
    }
  };

  if (!prediction) return null;

  return (
    <section className="mt-6 space-y-4">
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-lg font-semibold text-slate-100">
          Downloadable Report
        </h2>
        <button
          type="button"
          onClick={handleDownload}
          className="inline-flex items-center rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-50 hover:bg-slate-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
        >
          Download PDF
        </button>
      </div>

      <div
        id="prediction-report"
        className="bg-white text-slate-900 rounded-lg shadow-md p-4 space-y-3 absolute -left-[9999px] top-0 w-[210mm]"
      >
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-base font-semibold">
              Lung Disease Screening Report
            </h1>
            <p className="text-[11px] text-slate-600">
              Report ID: {prediction.id} •{" "}
              {formatDate(prediction.created_at)}
            </p>
          </div>
          <UrgencyBadge
            level={prediction.urgency_level}
            icon={prediction.urgency_icon}
            label={prediction.urgency_level.replace("_", " ")}
          />
        </header>

        {(prediction.patient_name || prediction.patient_age || prediction.patient_sex) && (
          <section className="grid grid-cols-3 gap-3 text-[11px] p-2 bg-slate-50 rounded border border-slate-200">
            {prediction.patient_name && (
              <div>
                <span className="font-semibold text-slate-800">Name:</span> {prediction.patient_name}
              </div>
            )}
            {prediction.patient_age && (
              <div>
                <span className="font-semibold text-slate-800">Age:</span> {prediction.patient_age}
              </div>
            )}
            {prediction.patient_sex && (
              <div>
                <span className="font-semibold text-slate-800">Sex:</span> {prediction.patient_sex}
              </div>
            )}
          </section>
        )}

        <section className="grid grid-cols-2 gap-3 text-[11px]">
          <div className="space-y-1">
            <h2 className="font-semibold text-slate-800 text-xs">
              Prediction Summary
            </h2>
            <p>
              <span className="font-semibold">Predicted class:</span>{" "}
              {prediction.predicted_class}
            </p>
            <p>
              <span className="font-semibold">Confidence:</span>{" "}
              {formatConfidence(prediction.confidence_score)}
            </p>
          </div>
          <div className="space-y-1">
            <h2 className="font-semibold text-slate-800 text-xs">
              Processing
            </h2>
            <p>
              <span className="font-semibold">Processing time:</span>{" "}
              {prediction.processing_time_ms?.toFixed(1)} ms
            </p>
            <p>
              <span className="font-semibold">Cached result:</span>{" "}
              {prediction.cached_result ? "Yes" : "No"}
            </p>
          </div>
        </section>

        <section className="grid grid-cols-2 gap-3 text-[11px]">
          <div>
            <h3 className="font-semibold text-xs text-slate-800">
              Immediate actions
            </h3>
            <ul className="list-disc list-inside space-y-0.5">
              {prediction.immediate_actions?.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-xs text-slate-800">
              Medical recommendations
            </h3>
            <ul className="list-disc list-inside space-y-0.5">
              {prediction.medical_recommendations?.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          </div>
        </section>

        <section className="grid grid-cols-2 gap-3 text-[11px]">
          <div>
            <h3 className="font-semibold text-xs text-slate-800">
              Lifestyle recommendations
            </h3>
            <ul className="list-disc list-inside space-y-0.5">
              {prediction.lifestyle_recommendations?.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-xs text-slate-800">
              Follow-up
            </h3>
            <p>{prediction.follow_up}</p>
          </div>
        </section>

        <footer className="border-t border-slate-200 pt-2 mt-1">
          <p className="text-[10px] text-slate-600">
            {prediction.disclaimer}
          </p>
        </footer>
      </div>
    </section>
  );
};

ReportGenerator.propTypes = {
  prediction: PropTypes.object
};

export default ReportGenerator;

