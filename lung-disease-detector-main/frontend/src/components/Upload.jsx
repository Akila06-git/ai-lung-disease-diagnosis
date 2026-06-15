import React, { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import toast from "react-hot-toast";
import { FiUploadCloud, FiUser } from "react-icons/fi";
import LoadingSpinner from "@components/common/LoadingSpinner";
import { useAuth } from "../context/AuthContext";
import { usePrediction } from "@hooks/usePrediction";
import {
  ACCEPTED_TYPES,
  MAX_FILE_SIZE_BYTES,
  isImageFile,
  isWithinSizeLimit,
  getImageDimensions,
  formatFileSize
} from "@utils/validators";

const MIN_DIM = 224;

const Upload = () => {
  const { file, setFile, isSubmitting, isPolling, submit } = usePrediction();
  const { user } = useAuth();
  const [preview, setPreview] = useState(null);
  const [dimError, setDimError] = useState("");

  // Patient details state
  const [patientName, setPatientName] = useState("");
  const [patientAge, setPatientAge] = useState("");
  const [patientSex, setPatientSex] = useState("");
  const [language, setLanguage] = useState("English");
  const [symptoms, setSymptoms] = useState("");

  const onDrop = useCallback(
    async (acceptedFiles) => {
      const picked = acceptedFiles[0];
      if (!picked) return;

      if (!isImageFile(picked)) {
        toast.error("Only JPG and PNG images are allowed.");
        return;
      }
      if (!isWithinSizeLimit(picked)) {
        toast.error("File too large. Maximum allowed size is 10MB.");
        return;
      }

      const isDicom = picked.name.toLowerCase().endsWith(".dcm") || picked.name.toLowerCase().endsWith(".dicom");

      if (!isDicom) {
        try {
          const { width, height } = await getImageDimensions(picked);
          if (width < MIN_DIM || height < MIN_DIM) {
            setDimError(`Image is too small (${width}x${height}). Minimum is ${MIN_DIM}x${MIN_DIM}px.`);
            toast.error("Image dimensions are too small for reliable analysis.");
            return;
          }
          setDimError("");
        } catch {
          toast.error("Could not read image dimensions.");
          return;
        }
        setPreview(URL.createObjectURL(picked));
      } else {
        setDimError("");
        setPreview("DICOM_PLACEHOLDER");
      }

      setFile(picked);
    },
    [setFile]
  );

  const {
    getRootProps,
    getInputProps,
    isDragActive,
    fileRejections
  } = useDropzone({
    onDrop,
    accept: {
      "image/jpeg": [".jpg", ".jpeg"],
      "image/png": [".png"],
      "application/dicom": [".dcm", ".dicom"],
      "": [".dcm", ".dicom"]
    },
    maxSize: MAX_FILE_SIZE_BYTES,
    multiple: false
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    await submit({
      patient_name: user?.is_superuser ? patientName : user?.username || "",
      patient_age: user?.is_superuser ? patientAge : "",
      patient_sex: patientSex,
      symptoms: symptoms,
      language: language
    });
  };

  return (
    <section aria-label="Upload chest X-ray for AI analysis" className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-slate-50">
          Upload Chest X-ray
        </h1>
        <p className="mt-1 text-sm text-slate-400 max-w-2xl">
          Securely upload a chest X-ray image to screen for COVID-19, Tuberculosis,
          Pneumonia, or confirm normal findings. Processing happens asynchronously;
          you can continue using the app while the AI runs.
        </p>
      </header>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Patient Details Section */}
        <div className="bg-surface rounded-xl p-6 border border-slate-700 shadow-card space-y-4">
          <h2 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
            <FiUser className="text-blue-400" /> Patient Details & NLP Options (Optional)
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">

            {/* Admins (Doctors) see the Name and Age fields */}
            {(user?.is_superuser || user?.role === 'DOCTOR') && (
              <>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={patientName}
                    onChange={(e) => setPatientName(e.target.value)}
                    className="w-full rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
                    placeholder="e.g. John Doe"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Age
                  </label>
                  <input
                    type="number"
                    value={patientAge}
                    onChange={(e) => setPatientAge(e.target.value)}
                    min="0"
                    max="150"
                    className="w-full rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
                    placeholder="e.g. 45"
                  />
                </div>
              </>
            )}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Sex
              </label>
              <select
                value={patientSex}
                onChange={(e) => setPatientSex(e.target.value)}
                className="w-full rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
              >
                <option value="">Select...</option>
                <option value="M">Male</option>
                <option value="F">Female</option>
                <option value="O">Other</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                AI Output Language
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
              >
                <option value="English">English</option>
                <option value="Spanish">Spanish</option>
                <option value="French">French</option>
                <option value="Hindi">Hindi</option>
                <option value="Mandarin">Mandarin</option>
                <option value="Arabic">Arabic</option>
                <option value="German">German</option>
                <option value="Tamil">Tamil</option>
              </select>
            </div>
            <div className="md:col-span-4">
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Symptoms (optional)
              </label>
              <textarea
                value={symptoms}
                onChange={(e) => setSymptoms(e.target.value)}
                className="w-full rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none h-20 resize-none"
                placeholder="Describe current symptoms (e.g. fever, cough, shortness of breath) for AI analysis..."
              />
            </div>
          </div>
        </div>

        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-6 bg-surface shadow-card cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 ${isDragActive ? "border-blue-500 bg-slate-900/50" : "border-slate-700 hover:border-slate-600 transition-colors"
            }`}
        >
          <input {...getInputProps()} aria-label="Upload chest X-ray image" />
          <div className="flex flex-col items-center gap-3 text-center">
            <div className="h-12 w-12 rounded-full bg-slate-800 flex items-center justify-center">
              <FiUploadCloud className="h-6 w-6 text-blue-400" aria-hidden="true" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-100">
                {isDragActive
                  ? "Drop the X-ray image here"
                  : "Drag and drop a chest X-ray, or click to browse"}
              </p>
              <p className="mt-1 text-xs text-slate-400">
                Accepted formats: JPG, PNG, DICOM (PACS) — Max size: 10MB
              </p>
            </div>
            {file && (
              <p className="mt-2 text-xs text-slate-300">
                Selected: <span className="font-semibold">{file.name}</span>{" "}
                <span className="text-slate-400">
                  ({formatFileSize(file.size)})
                </span>
              </p>
            )}
            {dimError && (
              <p className="mt-2 text-xs text-red-300" role="alert">
                {dimError}
              </p>
            )}
          </div>
        </div>

        {preview && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <figure className="bg-surface rounded-xl overflow-hidden border border-slate-800">
              {preview === "DICOM_PLACEHOLDER" ? (
                <div className="w-full h-64 bg-slate-900 flex flex-col items-center justify-center gap-3 border-b border-slate-800">
                  <div className="h-16 w-16 rounded-lg bg-blue-500/20 flex items-center justify-center">
                    <FiUploadCloud className="h-8 w-8 text-blue-400" />
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-semibold text-slate-100">DICOM Medical File</p>
                    <p className="text-[10px] text-slate-400 uppercase tracking-widest mt-1">PACS Standard Format</p>
                  </div>
                </div>
              ) : (
                <img
                  src={preview}
                  alt="Selected chest X-ray preview"
                  className="w-full h-64 object-contain bg-black"
                />
              )}
              <figcaption className="px-4 py-2 text-xs text-slate-400">
                {preview === "DICOM_PLACEHOLDER"
                  ? "DICOM metadata will be extracted automatically upon analysis."
                  : "Preview of the uploaded image. Ensure it is a clear, properly centered chest X-ray."}
              </figcaption>
            </figure>
            <div className="text-xs text-slate-400 space-y-2">
              <h2 className="text-sm font-semibold text-slate-100">
                Security & Privacy
              </h2>
              <ul className="list-disc list-inside space-y-1">
                <li>Images are validated server-side for type and size.</li>
                <li>Only anonymized X-rays should be uploaded.</li>
                <li>
                  This tool is for screening only and does not replace a medical
                  diagnosis.
                </li>
              </ul>
            </div>
          </div>
        )}

        <div className="flex items-center gap-3 mt-4">
          <button
            type="submit"
            className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white shadow-xl shadow-blue-500/20 hover:bg-blue-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-95"
            disabled={!file || isSubmitting || isPolling}
          >
            {isSubmitting || isPolling ? "Processing..." : "Analyze X-ray"}
          </button>
          {(isSubmitting || isPolling) && (
            <LoadingSpinner size="sm" label="Running AI analysis..." />
          )}
        </div>
      </form>
    </section>
  );
};

export default Upload;

