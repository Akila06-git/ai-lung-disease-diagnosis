import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { uploadImage, getTaskStatus } from "@services/api";
import { usePolling } from "./usePolling";

export const usePrediction = () => {
  const [file, setFile] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [predictionId, setPredictionId] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const navigate = useNavigate();

  const startPolling = useCallback(async () => {
    if (!taskId) return false;
    const { data } = await getTaskStatus(taskId, predictionId);
    if (data.status === "completed" && data.prediction) {
      setPrediction(data.prediction);
      navigate(`/result/${data.prediction.id}`, { state: { prediction: data.prediction } });
      return false;
    }
    if (data.status === "failed") {
      toast.error("Prediction failed. Please try again.");
      return false;
    }
    return true;
  }, [taskId, predictionId, navigate]);

  const { isPolling } = usePolling(startPolling, {
    enabled: !!taskId,
    interval: 1500,
    maxAttempts: 120
  });

  const submit = async (extraData = {}) => {
    if (!file) {
      toast.error("Please select an image first.");
      return;
    }
    setIsSubmitting(true);
    try {
      const { data } = await uploadImage(file, extraData);
      if (data.cached && data.prediction) {
        setPrediction(data.prediction);
        navigate(`/result/${data.prediction.id}`, { state: { prediction: data.prediction } });
      } else if (data.task_id) {
        setTaskId(data.task_id);
        if (data.prediction_id) setPredictionId(data.prediction_id);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return {
    file,
    setFile,
    isSubmitting,
    isPolling,
    prediction,
    submit
  };
};

