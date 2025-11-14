import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Brain, 
  Activity, 
  TrendingUp, 
  AlertTriangle,
  Target,
  Zap,
  Clock,
  Database,
  GitBranch,
  CheckCircle,
  XCircle
} from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, ScatterChart, Scatter, PieChart, Pie, Cell } from 'recharts'

// Mock SHAP data for feature importance
const featureImportance = [
  { name: 'RSI_14', importance: 0.234, color: '#3b82f6' },
  { name: 'MACD_signal', importance: 0.189, color: '#10b981' },
  { name: 'Volume_ratio', importance: 0.156, color: '#f59e0b' },
  { name: 'Price_momentum', importance: 0.134, color: '#ef4444' },
  { name: 'VWAP_deviation', importance: 0.112, color: '#8b5cf6' },
  { name: 'ATR_14', importance: 0.089, color: '#06b6d4' },
  { name: 'OBV_trend', importance: 0.067, color: '#84cc16' },
  { name: 'Bollinger_position', importance: 0.045, color: '#f97316' },
  { name: 'Sector_momentum', importance: 0.034, color: '#ec4899' },
  { name: 'Market_regime', importance: 0.023, color: '#6366f1' },
]

// Mock model performance data
const modelPerformance = [
  { metric: 'Accuracy', value: 0.847, target: 0.85, status: 'good' },
  { metric: 'Precision', value: 0.823, target: 0.80, status: 'excellent' },
  { metric: 'Recall', value: 0.789, target: 0.80, status: 'good' },
  { metric: 'F1-Score', value: 0.805, target: 0.80, status: 'excellent' },
  { metric: 'AUC-ROC', value: 0.912, target: 0.90, status: 'excellent' },
  { metric: 'Sharpe Ratio', value: 1.856, target: 1.50, status: 'excellent' },
]

// Mock prediction confidence distribution
const confidenceDistribution = [
  { range: '0.9-1.0', count: 45, accuracy: 0.956 },
  { range: '0.8-0.9', count: 78, accuracy: 0.872 },
  { range: '0.7-0.8', count: 123, accuracy: 0.789 },
  { range: '0.6-0.7', count: 89, accuracy: 0.674 },
  { range: '0.5-0.6', count: 34, accuracy: 0.523 },
]

// Mock model drift data
const driftData = [
  { date: '2024-09', accuracy: 0.856, prediction_drift: 0.023 },
  { date: '2024-10', accuracy: 0.842, prediction_drift: 0.031 },
  { date: '2024-11', accuracy: 0.847, prediction_drift: 0.028 },
  { date: '2024-12', accuracy: 0.851, prediction_drift: 0.025 },
]

// Mock sector performance by model
const sectorPerformance = [
  { sector: 'Technology', predictions: 234, accuracy: 0.891, avg_return: 4.2 },
  { sector: 'Healthcare', predictions: 156, accuracy: 0.823, avg_return: 3.8 },
  { sector: 'Finance', predictions: 189, accuracy: 0.856, avg_return: 3.5 },
  { sector: 'Energy', predictions: 98, accuracy: 0.798, avg_return: 5.1 },
  { sector: 'Consumer', predictions: 167, accuracy: 0.834, avg_return: 2.9 },
]

const modelVersions = [
  { version: 'v2.1.3', status: 'active', accuracy: 0.847, date: '2024-11-01' },
  { version: 'v2.1.2', status: 'deprecated', accuracy: 0.823, date: '2024-10-15' },
  { version: 'v2.1.1', status: 'deprecated', accuracy: 0.815, date: '2024-10-01' },
  { version: 'v2.1.0', status: 'deprecated', accuracy: 0.801, date: '2024-09-15' },
]

export default function InsightsPage() {
  const [selectedView, setSelectedView] = useState<'overview' | 'features' | 'performance' | 'drift'>('overview')
  const [selectedModel, setSelectedModel] = useState('v2.1.3')

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'excellent':
        return <CheckCircle className="w-5 h-5 text-green-400" />
      case 'good':
        return <Activity className="w-5 h-5 text-yellow-400" />
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-orange-400" />
      default:
        return <XCircle className="w-5 h-5 text-red-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'excellent':
        return 'text-green-400'
      case 'good':
        return 'text-yellow-400'
      case 'warning':
        return 'text-orange-400'
      default:
        return 'text-red-400'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Model Insights</h1>
          <p className="text-muted-foreground mt-1">AI model performance and feature analysis</p>
        </div>
        <div className="flex items-center space-x-3">
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="px-3 py-2 bg-card border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {modelVersions.map(version => (
              <option key={version.version} value={version.version}>
                {version.version} {version.status === 'active' ? '(Active)' : ''}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-card border border-border rounded-xl p-2">
        <div className="flex space-x-1">
          {[
            { id: 'overview', label: 'Overview', icon: Brain },
            { id: 'features', label: 'Features', icon: Database },
            { id: 'performance', label: 'Performance', icon: Activity },
            { id: 'drift', label: 'Model Drift', icon: GitBranch },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSelectedView(tab.id as any)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                selectedView === tab.id
                  ? 'bg-blue-500/20 text-blue-400'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted/20'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Overview Tab */}
      {selectedView === 'overview' && (
        <div className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <motion.div
              whileHover={{ scale: 1.02 }}
              className="bg-card border border-border rounded-xl p-6 shadow-sm"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-muted-foreground">Model Accuracy</h3>
                <Brain className="w-5 h-5 text-muted-foreground" />
              </div>
              <p className="text-2xl font-bold text-foreground">84.7%</p>
              <div className="flex items-center mt-2 text-sm text-gain">
                <TrendingUp className="w-4 h-4 mr-1" />
                <span>+2.3% from last version</span>
              </div>
            </motion.div>

            <motion.div
              whileHover={{ scale: 1.02 }}
              className="bg-card border border-border rounded-xl p-6 shadow-sm"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-muted-foreground">Active Signals</h3>
                <Zap className="w-5 h-5 text-muted-foreground" />
              </div>
              <p className="text-2xl font-bold text-foreground">247</p>
              <div className="flex items-center mt-2 text-sm text-muted-foreground">
                <Clock className="w-4 h-4 mr-1" />
                <span>Updated 2 min ago</span>
              </div>
            </motion.div>

            <motion.div
              whileHover={{ scale: 1.02 }}
              className="bg-card border border-border rounded-xl p-6 shadow-sm"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-muted-foreground">Avg Confidence</h3>
                <Target className="w-5 h-5 text-muted-foreground" />
              </div>
              <p className="text-2xl font-bold text-foreground">78.3%</p>
              <div className="flex items-center mt-2 text-sm text-gain">
                <TrendingUp className="w-4 h-4 mr-1" />
                <span>Optimal range</span>
              </div>
            </motion.div>

            <motion.div
              whileHover={{ scale: 1.02 }}
              className="bg-card border border-border rounded-xl p-6 shadow-sm"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-muted-foreground">Data Drift</h3>
                <AlertTriangle className="w-5 h-5 text-muted-foreground" />
              </div>
              <p className="text-2xl font-bold text-yellow-400">2.8%</p>
              <div className="flex items-center mt-2 text-sm text-yellow-400">
                <Activity className="w-4 h-4 mr-1" />
                <span>Within threshold</span>
              </div>
            </motion.div>
          </div>

          {/* Model Performance Grid */}
          <div className="bg-card border border-border rounded-xl p-6">
            <h3 className="text-lg font-semibold text-foreground mb-6">Model Performance Metrics</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {modelPerformance.map((metric, index) => (
                <div key={index} className="flex items-center justify-between p-4 bg-muted/10 rounded-lg">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">{metric.metric}</p>
                    <p className="text-xl font-bold text-foreground">
                      {(metric.value * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="flex flex-col items-end">
                    {getStatusIcon(metric.status)}
                    <p className={`text-xs mt-1 ${getStatusColor(metric.status)}`}>
                      Target: {(metric.target * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Sector Performance */}
          <div className="bg-card border border-border rounded-xl p-6">
            <h3 className="text-lg font-semibold text-foreground mb-6">Performance by Sector</h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-muted/20">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Sector
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Predictions
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Accuracy
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Avg Return
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {sectorPerformance.map((sector, index) => (
                    <tr key={index} className="hover:bg-muted/10 transition-colors">
                      <td className="px-4 py-4 whitespace-nowrap text-sm font-medium text-foreground">
                        {sector.sector}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-muted-foreground">
                        {sector.predictions}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <span className={`text-sm font-medium ${
                          sector.accuracy >= 0.85 ? 'text-green-400' :
                          sector.accuracy >= 0.80 ? 'text-yellow-400' : 'text-red-400'
                        }`}>
                          {(sector.accuracy * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-foreground">
                        {sector.avg_return.toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Features Tab */}
      {selectedView === 'features' && (
        <div className="space-y-6">
          <div className="bg-card border border-border rounded-xl p-6">
            <h3 className="text-lg font-semibold text-foreground mb-6">Feature Importance (SHAP Analysis)</h3>
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={featureImportance} layout="horizontal">
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis type="number" stroke="#6b7280" />
                  <YAxis 
                    type="category" 
                    dataKey="name" 
                    stroke="#6b7280"
                    width={120}
                    fontSize={12}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1e293b',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      color: '#f1f5f9'
                    }}
                    formatter={(value: any) => [`${(value * 100).toFixed(1)}%`, 'Importance']}
                  />
                  <Bar 
                    dataKey="importance" 
                    fill={(entry: any) => entry.color}
                  >
                    {featureImportance.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-card border border-border rounded-xl p-6">
              <h3 className="text-lg font-semibold text-foreground mb-6">Confidence vs Accuracy</h3>
              <ResponsiveContainer width="100%" height={250}>
                <ScatterChart data={confidenceDistribution}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis 
                    dataKey="range" 
                    stroke="#6b7280"
                    fontSize={12}
                  />
                  <YAxis 
                    stroke="#6b7280"
                    fontSize={12}
                    tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1e293b',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      color: '#f1f5f9'
                    }}
                    formatter={(value: any, name: string) => [
                      name === 'accuracy' ? `${(value * 100).toFixed(1)}%` : value,
                      name === 'accuracy' ? 'Accuracy' : 'Count'
                    ]}
                  />
                  <Scatter 
                    dataKey="accuracy" 
                    fill="#3b82f6"
                    name="accuracy"
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-card border border-border rounded-xl p-6">
              <h3 className="text-lg font-semibold text-foreground mb-6">Feature Correlation Matrix</h3>
              <div className="grid grid-cols-4 gap-2">
                {['RSI', 'MACD', 'Volume', 'Price'].map((feature, i) => (
                  <div key={i} className="text-xs text-muted-foreground text-center mb-2">
                    {feature}
                  </div>
                ))}
                {[1.0, 0.23, -0.15, 0.67, 0.23, 1.0, 0.45, 0.12, -0.15, 0.45, 1.0, -0.08, 0.67, 0.12, -0.08, 1.0].map((corr, i) => (
                  <div
                    key={i}
                    className="aspect-square rounded flex items-center justify-center text-xs font-medium"
                    style={{
                      backgroundColor: corr > 0 ? 
                        `rgba(59, 130, 246, ${Math.abs(corr)})` : 
                        `rgba(239, 68, 68, ${Math.abs(corr)})`,
                      color: Math.abs(corr) > 0.5 ? 'white' : '#1f2937'
                    }}
                  >
                    {corr.toFixed(2)}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Performance Tab */}
      {selectedView === 'performance' && (
        <div className="space-y-6">
          <div className="bg-card border border-border rounded-xl p-6">
            <h3 className="text-lg font-semibold text-foreground mb-6">Model Performance Over Time</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={driftData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis 
                  dataKey="date" 
                  stroke="#6b7280"
                  fontSize={12}
                />
                <YAxis 
                  stroke="#6b7280"
                  fontSize={12}
                  tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    color: '#f1f5f9'
                  }}
                  formatter={(value: any) => [`${(value * 100).toFixed(1)}%`, 'Accuracy']}
                />
                <Line 
                  type="monotone" 
                  dataKey="accuracy" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6', r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-card border border-border rounded-xl p-6">
              <h3 className="text-lg font-semibold text-foreground mb-6">Model Versions</h3>
              <div className="space-y-4">
                {modelVersions.map((version, index) => (
                  <div key={index} className="flex items-center justify-between p-4 bg-muted/10 rounded-lg">
                    <div>
                      <p className="text-sm font-medium text-foreground">{version.version}</p>
                      <p className="text-xs text-muted-foreground">Deployed {version.date}</p>
                    </div>
                    <div className="flex items-center space-x-3">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        version.status === 'active' 
                          ? 'bg-green-500/20 text-green-400' 
                          : 'bg-gray-500/20 text-gray-400'
                      }`}>
                        {version.status}
                      </span>
                      <span className="text-sm font-medium text-foreground">
                        {(version.accuracy * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-card border border-border rounded-xl p-6">
              <h3 className="text-lg font-semibold text-foreground mb-6">Training Pipeline Status</h3>
              <div className="space-y-4">
                {[
                  { stage: 'Data Collection', status: 'completed', duration: '15 min' },
                  { stage: 'Feature Engineering', status: 'completed', duration: '8 min' },
                  { stage: 'Model Training', status: 'running', duration: '45 min' },
                  { stage: 'Validation', status: 'pending', duration: '12 min' },
                  { stage: 'Deployment', status: 'pending', duration: '5 min' },
                ].map((stage, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`w-3 h-3 rounded-full ${
                        stage.status === 'completed' ? 'bg-green-500' :
                        stage.status === 'running' ? 'bg-yellow-500 animate-pulse' :
                        'bg-gray-500'
                      }`} />
                      <span className="text-sm text-foreground">{stage.stage}</span>
                    </div>
                    <span className="text-sm text-muted-foreground">{stage.duration}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Model Drift Tab */}
      {selectedView === 'drift' && (
        <div className="space-y-6">
          <div className="bg-card border border-border rounded-xl p-6">
            <h3 className="text-lg font-semibold text-foreground mb-6">Model Drift Analysis</h3>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <h4 className="text-sm font-semibold text-foreground mb-4">Prediction Drift</h4>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={driftData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis 
                      dataKey="date" 
                      stroke="#6b7280"
                      fontSize={12}
                    />
                    <YAxis 
                      stroke="#6b7280"
                      fontSize={12}
                      tickFormatter={(value) => value.toFixed(3)}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#1e293b',
                        border: '1px solid #334155',
                        borderRadius: '8px',
                        color: '#f1f5f9'
                      }}
                      formatter={(value: any) => [value.toFixed(3), 'Drift Score']}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="prediction_drift" 
                      stroke="#f59e0b" 
                      strokeWidth={2}
                      dot={{ fill: '#f59e0b', r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-foreground mb-4">Drift Thresholds</h4>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
                    <span className="text-sm text-foreground">Data Quality</span>
                    <span className="text-sm font-medium text-green-400">Normal</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                    <span className="text-sm text-foreground">Feature Drift</span>
                    <span className="text-sm font-medium text-yellow-400">Warning</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
                    <span className="text-sm text-foreground">Concept Drift</span>
                    <span className="text-sm font-medium text-green-400">Normal</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-card border border-border rounded-xl p-6">
            <h3 className="text-lg font-semibold text-foreground mb-6">Drift Detection Alerts</h3>
            <div className="space-y-4">
              {[
                { 
                  type: 'Feature Drift', 
                  severity: 'warning', 
                  message: 'Volume_ratio feature showing significant drift (p-value: 0.023)',
                  timestamp: '2024-11-13 14:30:00'
                },
                { 
                  type: 'Performance Drop', 
                  severity: 'info', 
                  message: 'Accuracy decreased by 1.2% in last 24 hours',
                  timestamp: '2024-11-13 12:15:00'
                },
                { 
                  type: 'Data Quality', 
                  severity: 'error', 
                  message: 'Missing data in RSI_14 feature for 15 symbols',
                  timestamp: '2024-11-13 10:45:00'
                },
              ].map((alert, index) => (
                <div key={index} className={`flex items-start space-x-3 p-4 rounded-lg ${
                  alert.severity === 'error' ? 'bg-red-500/10 border border-red-500/20' :
                  alert.severity === 'warning' ? 'bg-yellow-500/10 border border-yellow-500/20' :
                  'bg-blue-500/10 border border-blue-500/20'
                }`}>
                  <div className="flex-shrink-0 mt-1">
                    {alert.severity === 'error' ? 
                      <XCircle className="w-5 h-5 text-red-400" /> :
                      alert.severity === 'warning' ?
                      <AlertTriangle className="w-5 h-5 text-yellow-400" /> :
                      <Activity className="w-5 h-5 text-blue-400" />
                    }
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-foreground">{alert.type}</p>
                    <p className="text-sm text-muted-foreground mt-1">{alert.message}</p>
                    <p className="text-xs text-muted-foreground mt-2">{alert.timestamp}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}