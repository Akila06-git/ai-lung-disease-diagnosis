import React from "react";
import PropTypes from "prop-types";

const levelStyles = {
  HIGH: "bg-red-500/10 text-red-300 border-red-500/60",
  MEDIUM_HIGH: "bg-orange-500/10 text-orange-300 border-orange-500/60",
  MEDIUM: "bg-yellow-500/10 text-yellow-200 border-yellow-500/60",
  LOW: "bg-emerald-500/10 text-emerald-300 border-emerald-500/60"
};

const UrgencyBadge = ({ level, icon, label }) => {
  const base =
    "inline-flex items-center gap-1 rounded-full border px-3 py-1 text-xs font-semibold";
  const cls = `${base} ${levelStyles[level] || levelStyles.MEDIUM}`;

  return (
    <span className={cls} aria-label={`Urgency level: ${label}`} role="status">
      <span aria-hidden="true">{icon}</span>
      <span>{label}</span>
    </span>
  );
};

UrgencyBadge.propTypes = {
  level: PropTypes.string.isRequired,
  icon: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired
};

export default UrgencyBadge;

