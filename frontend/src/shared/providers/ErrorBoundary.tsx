import { Component, ErrorInfo, ReactNode } from "react";

type Props = {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
};

type State = {
  error: Error | null;
  errorInfo: ErrorInfo | null;
};

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null, errorInfo: null };

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ error, errorInfo });
    this.props.onError?.(error, errorInfo);
  }

  render() {
    const { error, errorInfo } = this.state;

    if (error === null || errorInfo === null) {
      return this.props.children;
    }

    return this.props.fallback ?? <></>;
  }
}
