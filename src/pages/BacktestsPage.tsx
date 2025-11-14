import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  Play, 
  Pause, 
  Trash2, 
  FileText, 
  TrendingUp, 
  Calendar,
  Target,
  BarChart3,
  Plus,
  Download,
  Eye
} from 'lucide-react'

interface Backtest {
  id: number
  name: string
  strategy_type: string
  symbols: string[]
  start_date: string
  end_date: string
  status: string
  total_return?: number
  sharpe_ratio?: number
  max_drawdown?: number
  win_rate?: number
  total_trades?: number
  created_at: string
}

interface StrategyTemplate {
  id: number
  name: string
  description: string
  strategy_type: string
  parameters: any
}

const mockBacktests: Backtest[] = [
  {
    id: 1,
    name: "Moving Average Crossover - Tech Stocks",
    strategy_type: "MOVING_AVERAGE",
    symbols: ["AAPL", "MSFT", "GOOGL", "NVDA"],
    start_date: "2024-01-01",
    end_date: "2024-11-01",
    status: "COMPLETED",
    total_return: 24.5,
    sharpe_ratio: 1.85,
    max_drawdown: -12.3,
    win_rate: 68.5,
    total_trades: 47,
    created_at: "2024-11-10T10:30:00Z"
  },
  {
    id: 2,
    name: "RSI Divergence Strategy",
    strategy_type: "RSI_DIVERGENCE",
    symbols: ["AAPL", "MSFT", "TSLA", "AMZN"],
    start_date: "2024-02-01",
    end_date: "2024-11-01",
    status: "COMPLETED",
    total_return: 18.7,
    sharpe_ratio: 1.42,
    max_drawdown: -15.8,
    win_rate: 62.1,
    total_trades: 58,
    created_at: "2024-11-09T14:20:00Z"
  },
  {
    id: 3,
    name: "MACD Crossover - Financial Sector",
    strategy_type: "MACD_CROSSOVER",
    symbols: ["JPM", "BAC", "WFC", "GS"],
    start_date: "2024-03-01",
    end_date: "2024-11-01",
    status: "RUNNING",
    created_at: "2024-11-12T09:15:00Z"
  },
  {
    id: 4,
    name: "Bollinger Bands Mean Reversion",
    strategy_type: "BOLLINGER_BANDS",
    symbols: ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
    start_date: "2024-01-01",
    end_date: "2024-11-01",
    status: "PENDING",
    created_at: "2024-11-13T11:45:00Z"
  }
]

const mockTemplates: StrategyTemplate[] = [
  {
    id: 1,
    name: "Moving Average Crossover",
    description: "Classic moving average crossover strategy with customizable periods",
    strategy_type: "MOVING_AVERAGE",
    parameters: {
      short_ma: 20,
      long_ma: 50,
      use_ema: false
    }
  },
  {
    id: 2,
    name: "RSI Divergence",
    description: "RSI-based mean reversion strategy with oversold/overbought signals",
    strategy_type: "RSI_DIVERGENCE",
    parameters: {
      rsi_period: 14,
      oversold_level: 30,
      overbought_level: 70
    }
  },
  {
    id: 3,
    name: "MACD Crossover",
    description: "MACD signal line crossover strategy for trend following",
    strategy_type: "MACD_CROSSOVER",
    parameters: {
      fast_period: 12,
      slow_period: 26,
      signal_period: 9
    }
  },
  {
    id: 4,
    name: "Bollinger Bands",
    description: "Mean reversion strategy using Bollinger Bands",
    strategy_type: "BOLLINGER_BANDS",
    parameters: {
      period: 20,
      std_dev: 2.0,
      mean_reversion: true
    }
  }
]

export default function BacktestsPage() {
  const [backtests, setBacktests] = useState<Backtest[]>(mockBacktests)
  const [templates, setTemplates] = useState<StrategyTemplate[]>(mockTemplates)
  const [selectedStrategy, setSelectedStrategy] = useState<string>('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [loading, setLoading] = useState(false)

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return 'text-green-400 bg-green-500/20'
      case 'RUNNING':
        return 'text-yellow-400 bg-yellow-500/20'
      case 'PENDING':
        return 'text-blue-400 bg-blue-500/20'
      case 'FAILED':
        return 'text-red-400 bg-red-500/20'
      default:
        return 'text-gray-400 bg-gray-500/20'
    }
  }

  const getStrategyIcon = (strategyType: string) => {
    switch (strategyType) {
      case 'MOVING_AVERAGE':
        return <TrendingUp className="w-4 h-4" />
      case 'RSI_DIVERGENCE':
        return <Target className="w-4 h-4" />
      case 'MACD_CROSSOVER':
        return <BarChart3 className="w-4 h-4" />
      case 'BOLLINGER_BANDS':
        return <Calendar className="w-4 h-4" />
      default:
        return <TrendingUp className="w-4 h-4" />
    }
  }

  const handleCreateBacktest = () => {
    setShowCreateModal(true)
  }

  const handleRunBacktest = async (backtestId: number) => {
    setLoading(true)
    // In a real app, this would call the API
    setTimeout(() => {
      setBacktests(prev => prev.map(bt => 
        bt.id === backtestId ? { ...bt, status: 'RUNNING' } : bt
      ))
      setLoading(false)
    }, 1000)
  }

  const handleStopBacktest = async (backtestId: number) => {
    setLoading(true)
    // In a real app, this would call the API
    setTimeout(() => {
      setBacktests(prev => prev.map(bt => 
        bt.id === backtestId ? { ...bt, status: 'PENDING' } : bt
      ))
      setLoading(false)
    }, 1000)
  }

  const handleDeleteBacktest = async (backtestId: number) => {
    setBacktests(prev => prev.filter(bt => bt.id !== backtestId))
  }

  const handleViewResults = (backtestId: number) => {
    // Navigate to results page or show modal
    console.log('View results for backtest:', backtestId)
  }

  const handleDownloadReport = async (backtestId: number) => {
    // In a real app, this would download the report
    console.log('Download report for backtest:', backtestId)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Backtesting</h1>
          <p className="text-muted-foreground mt-1">Test and optimize your trading strategies</p>
        </div>
        <button
          onClick={handleCreateBacktest}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>New Backtest</span>
        </button>
      </div>

      {/* Strategy Templates */}
      <div className="bg-card border border-border rounded-xl p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">Strategy Templates</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {templates.map((template) => (
            <div
              key={template.id}
              className="p-4 bg-muted/20 border border-border rounded-lg hover:border-blue-500/50 transition-colors cursor-pointer"
              onClick={() => setSelectedStrategy(template.strategy_type)}
            >
              <div className="flex items-center space-x-2 mb-2">
                {getStrategyIcon(template.strategy_type)}
                <h4 className="font-medium text-foreground">{template.name}</h4>
              </div>
              <p className="text-sm text-muted-foreground">{template.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Backtests List */}
      <div className="bg-card border border-border rounded-xl overflow-hidden">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold text-foreground">Your Backtests</h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/20">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Strategy
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Symbols
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Period
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Return
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Sharpe
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Trades
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {backtests.map((backtest) => (
                <tr key={backtest.id} className="hover:bg-muted/10 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-foreground">{backtest.name}</div>
                      <div className="text-sm text-muted-foreground">
                        {new Date(backtest.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      {getStrategyIcon(backtest.strategy_type)}
                      <span className="text-sm text-foreground">{backtest.strategy_type}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-foreground">
                      {backtest.symbols.slice(0, 3).join(', ')}
                      {backtest.symbols.length > 3 && ` +${backtest.symbols.length - 3}`}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                    {backtest.start_date} - {backtest.end_date}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(backtest.status)}`}>
                      {backtest.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    {backtest.total_return !== undefined ? (
                      <span className={backtest.total_return >= 0 ? 'text-gain' : 'text-loss'}>
                        {backtest.total_return >= 0 ? '+' : ''}{backtest.total_return.toFixed(2)}%
                      </span>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                    {backtest.sharpe_ratio !== undefined ? backtest.sharpe_ratio.toFixed(2) : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                    {backtest.total_trades !== undefined ? backtest.total_trades : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      {backtest.status === 'PENDING' && (
                        <button
                          onClick={() => handleRunBacktest(backtest.id)}
                          disabled={loading}
                          className="p-2 text-green-400 hover:text-green-300 hover:bg-green-500/20 rounded-lg transition-colors"
                          title="Run Backtest"
                        >
                          <Play className="w-4 h-4" />
                        </button>
                      )}
                      {backtest.status === 'RUNNING' && (
                        <button
                          onClick={() => handleStopBacktest(backtest.id)}
                          disabled={loading}
                          className="p-2 text-yellow-400 hover:text-yellow-300 hover:bg-yellow-500/20 rounded-lg transition-colors"
                          title="Stop Backtest"
                        >
                          <Pause className="w-4 h-4" />
                        </button>
                      )}
                      {backtest.status === 'COMPLETED' && (
                        <>
                          <button
                            onClick={() => handleViewResults(backtest.id)}
                            className="p-2 text-blue-400 hover:text-blue-300 hover:bg-blue-500/20 rounded-lg transition-colors"
                            title="View Results"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDownloadReport(backtest.id)}
                            className="p-2 text-purple-400 hover:text-purple-300 hover:bg-purple-500/20 rounded-lg transition-colors"
                            title="Download Report"
                          >
                            <Download className="w-4 h-4" />
                          </button>
                        </>
                      )}
                      <button
                        onClick={() => handleDeleteBacktest(backtest.id)}
                        className="p-2 text-red-400 hover:text-red-300 hover:bg-red-500/20 rounded-lg transition-colors"
                        title="Delete Backtest"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Backtest Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <motion.div
            initial={{ scale: 0.95 }}
            animate={{ scale: 1 }}
            className="bg-card border border-border rounded-xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto"
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-foreground">Create New Backtest</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-2 hover:bg-muted/20 rounded-lg transition-colors"
              >
                <Plus className="w-5 h-5 transform rotate-45" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-2">
                  Backtest Name
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 bg-muted/20 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter backtest name"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-2">
                  Strategy Type
                </label>
                <select
                  value={selectedStrategy}
                  onChange={(e) => setSelectedStrategy(e.target.value)}
                  className="w-full px-3 py-2 bg-muted/20 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select a strategy</option>
                  {templates.map((template) => (
                    <option key={template.id} value={template.strategy_type}>
                      {template.name}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-2">
                  Description
                </label>
                <textarea
                  className="w-full px-3 py-2 bg-muted/20 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  rows={3}
                  placeholder="Describe your backtest strategy..."
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-2">
                    Start Date
                  </label>
                  <input
                    type="date"
                    className="w-full px-3 py-2 bg-muted/20 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-2">
                    End Date
                  </label>
                  <input
                    type="date"
                    className="w-full px-3 py-2 bg-muted/20 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-2">
                  Symbols (comma-separated)
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 bg-muted/20 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="AAPL, MSFT, GOOGL, NVDA"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-2">
                  Initial Capital ($)
                </label>
                <input
                  type="number"
                  defaultValue="100000"
                  className="w-full px-3 py-2 bg-muted/20 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    // Handle create logic
                    setShowCreateModal(false)
                  }}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  Create Backtest
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}