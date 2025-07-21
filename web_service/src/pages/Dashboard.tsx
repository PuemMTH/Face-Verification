import React, { useState } from 'react';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { Camera, Upload, AlertCircle, Loader2 } from 'lucide-react';
import { uploadImage } from '../services/api';

export const Dashboard = () => {
  const [image, setImage] = useState<File | null>(null);
  const [result, setResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImage(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResult(null);
      setError(null);
    }
  };

  const handleUpload = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!image) return;

    setLoading(true);
    setError(null);

    try {
      const response = await uploadImage(image);
      setResult(response.data); // Always show JSON, regardless of status
    } catch (error) {
      console.error('Upload failed:', error);
      setError(error instanceof Error ? error.message : 'Unknown error occurred');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  // Helper: get color by status code/result
  const getResultColor = (result: any) => {
    // If result is null, fallback
    if (!result) return 'bg-base-300 border-base-400';
    // If result has status and status.success (API v2)
    if (result?.prediction?.status?.success !== undefined) {
      return result.prediction.status.success
        ? 'bg-green-100 border-green-400'
        : 'bg-error/20 border-error';
    }
    // If result has OK (API v1)
    if (result?.OK !== undefined) {
      return result.OK
        ? 'bg-green-100 border-green-400'
        : 'bg-error/20 border-error';
    }
    // fallback
    return 'bg-base-300 border-base-400';
  };

  // Helper: get status message
  const getResultStatusText = (result: any) => {
    if (!result) return null;
    if (result?.prediction?.status?.success !== undefined) {
      return result.prediction.status.success
        ? 'Success'
        : 'Failed';
    }
    if (result?.OK !== undefined) {
      return result.OK
        ? 'Success'
        : 'Failed';
    }
    return null;
  };

  // Helper: get status color
  const getResultStatusTextColor = (result: any) => {
    if (!result) return '';
    if (result?.prediction?.status?.success !== undefined) {
      return result.prediction.status.success
        ? 'text-green-700'
        : 'text-error';
    }
    if (result?.OK !== undefined) {
      return result.OK
        ? 'text-green-700'
        : 'text-error';
    }
    return '';
  };

  return (
    <div className="min-h-screen from-base-300 to-base-100 p-4 md:p-8 duration-300">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl md:text-4xl font-bold text-base-content mb-8">
          Face Verification
        </h1>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
          <div className="bg-base-200 rounded-xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 border border-base-300 h-fit">
            <div className="flex items-center mb-6">
              <Camera className="w-6 h-6 text-primary mr-2" />
              <h2 className="text-xl font-semibold text-base-content">Upload Image</h2>
            </div>
            <form onSubmit={handleUpload}>
              <div className="mb-6">
                <label className="relative group cursor-pointer">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageChange}
                    className="hidden"
                  />
                  <div className="h-32 border-2 border-dashed border-base-300 rounded-lg flex items-center justify-center bg-base-100/50 group-hover:border-primary transition-all duration-300">
                    <div className="text-center">
                      <Upload className="w-8 h-8 text-base-content/60 mb-2 mx-auto group-hover:text-primary transition-colors duration-300" />
                      <span className="text-sm text-base-content/60 group-hover:text-primary transition-colors duration-300">
                        Click to select image
                      </span>
                    </div>
                  </div>
                </label>
              </div>

              <button
                type="submit"
                disabled={!image || loading}
                className="btn btn-primary w-full"
              >
                {loading ? (
                  <LoadingSpinner size="sm" />
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    <span>{loading ? 'Analyzing...' : 'Analyze Image'}</span>
                  </>
                )}
              </button>
            </form>
          </div>

          <div className="md:col-span-2 bg-base-200 rounded-xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 border border-base-300">
            <h2 className="text-xl font-semibold text-base-content mb-6">Analysis Results</h2>
            
            <div className="space-y-6">
            {previewUrl && (
                <div className="rounded-lg overflow-hidden bg-base-300 p-1 transition-colors duration-300">
                  <h4 className="text-lg font-medium mb-2">Preview Image</h4>
                  <img
                    src={previewUrl}
                    alt="Preview"
                    className="w-full rounded-lg object-contain max-h-96"
                  />
                </div>
              )}

              {error && (
                <div className="bg-error/20 border border-error rounded-lg p-4 flex items-start animate-fadeIn">
                  <AlertCircle className="w-5 h-5 text-error mr-2 flex-shrink-0 mt-0.5" />
                  <p className="text-error">{error}</p>
                </div>
              )}

              {loading && !error && !result && (
                <div className="bg-green-500/20 border border-green-500 rounded-lg p-4 flex items-start animate-fadeIn">
                  <Loader2 className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5 animate-spin" />
                  <p className="text-green-500">Analyzing image...</p>
                </div>
              )}

              {/* Show JSON result if available */}
              {result && (
                <div className={`${getResultColor(result)} border rounded-lg p-4 animate-fadeIn`}>
                  <div className="flex items-center mb-2">
                    <h4 className="text-lg font-medium mr-2">API Response</h4>
                    {getResultStatusText(result) && (
                      <span className={`ml-2 px-2 py-0.5 rounded text-xs font-semibold ${getResultStatusTextColor(result)} bg-white/60`}>
                        {getResultStatusText(result)}
                      </span>
                    )}
                  </div>
                  <pre className="text-xs whitespace-pre-wrap break-all">
                    {JSON.stringify(result, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};