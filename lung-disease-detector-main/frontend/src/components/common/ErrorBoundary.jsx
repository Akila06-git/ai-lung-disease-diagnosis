import React from "react";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    // In production you could send this to Sentry
    console.error("ErrorBoundary caught an error", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          className="rounded-lg border border-red-500 bg-red-950/40 p-4 text-sm text-red-100"
          role="alert"
        >
          <h2 className="font-semibold mb-1">Something went wrong.</h2>
          <p>Please refresh the page or try your action again.</p>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

