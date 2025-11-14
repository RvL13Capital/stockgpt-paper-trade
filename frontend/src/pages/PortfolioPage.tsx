import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Target,
  StopCircle,
  Calendar,
  PieChart,
  BarChart3,
  Activity
} from 'lucide-react'
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

interface Position {
  id: string
  symbol: string
  company: string
  quantity: number
  avgCost: number
  currentPrice: number
  marketValue: number
  unrealizedPnL: number
  unrealizedPnLPercent: number
  targetPrice: number
  stopLoss: number
  sector: string
  entryDate: string
  lastSignal: 'BUY' | 'SELL' | 'HOLD'
  confidence: number
}

const mockPositions: Position[] = [
  {
    id: '1',
    symbol: 'AAPL',
    company: 'Apple Inc.',
    quantity: 100,
    avgCost: 170.50,
    currentPrice: 175.43,
    marketValue: 17543,
    unrealizedPnL: 493,
    unrealizedPnLPercent: 2.89,
    targetPrice: 185.00,
    stopLoss: 165.00,
    sector: 'Technology',
    entryDate: '2024-10-15',
    lastSignal: 'BUY',
    confidence: 0.87
  },
  {
    id: '2',
    symbol: 'MSFT',
    company: 'Microsoft Corporation',
    quantity: 50,
    avgCost: 365.20,
    currentPrice: 378.85,
    marketValue: 18942.50,
    unrealizedPnL: 682.50,
    unrealizedPnLPercent: 3.74,
    targetPrice: 395.00,
    stopLoss: 350.00,
    sector: 'Technology',
    entryDate: '2024-10-20',
    lastSignal: 'BUY',
    confidence: 0.92
  },
  {
    id: '3',
    symbol: 'GOOGL',
    company: 'Alphabet Inc.',
    quantity: 75,
    avgCost: 145.80,
    currentPrice: 142.56,
    marketValue: 10692,
    unrealizedPnL: -243,
    unrealizedPnLPercent: -1.67,
    targetPrice: 155.00,
    stopLoss: 135.00,
    sector: 'Technology',
    entryDate: '2024-11-01',
    lastSignal: 'HOLD',
    confidence: 0.78
  },
  {
    id: '4',
    symbol: 'NVDA',
    company: 'NVIDIA Corporation',
    quantity: 25,
    avgCost: 480.00,
    currentPrice: 495.22,
    marketValue: 12380.50,
    unrealizedPnL: 380.50,
    unrealizedPnLPercent: 3.17,
    targetPrice: 520.00,
    stopLoss: 450.00,
    sector: 'Technology',
    entryDate: '2024-10-25',
    lastSignal: 'BUY',
    confidence: 0.89
  },
  {
    id: '5',
    symbol: 'JPM',
    company: 'JPMorgan Chase & Co.',
    quantity: 80,
    avgCost: 165.40,
    currentPrice: 168.23,
    marketValue: 13458.40,
    unrealizedPnL: 226.40,
    unrealizedPnLPercent: 1.71,
    targetPrice: 178.00,
    stopLoss: 158.00,
    sector: 'Finance',
    entryDate: '2024-11-05',
    lastSignal: 'BUY',
    confidence: 0.84
  },
]

const portfolioStats = {
  totalValue: 73016.40,
  totalPnL: 1539.40,
  totalPnLPercent: 2.15,
  dayChange: 1250.30,
  dayChangePercent: 1.74,
  cash: 25000.00,
  invested: 73016.40,
  totalEquity: 98016.40
}

const sectorAllocation = [
  { name: 'Technology', value: 59557.50, percentage: 81.6, color: '#3b82f6' },
  { name: 'Finance', value: 13458.40, percentage: 18.4, color: '#10b981' },
]

const performanceData = [
  { date: '2024-10-15', value: 70000 },
  { date: '2024-10-20', value: 71200 },
  { date: '2024-10-25', value: 72500 },
  { date: '2024-10-30', value: 71800 },
  { date: '2024-11-05', value: 73500 },
  { date: '2024-11-10', value: 72800 },
  { date: '2024-11-13', value: 73016.40 },
]

export default function PortfolioPage() {
  const [selectedPosition, setSelectedPosition] = useState<string | null>(null)

  const getPnLColor = (pnl: number) => {
    return pnl >= 0 ? 'text-gain' : 'text-loss'
  }

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'BUY': return 'text-green-400 bg-green-500/20'
      case 'SELL': return 'text-red-400 bg-red-500/20'
      case 'HOLD': return 'text-yellow-400 bg-yellow-500/20'
      default: return 'text-gray-400 bg-gray-500/20'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Portfolio</h1>
          <p className="text-muted-foreground mt-1">Track your positions and performance</p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 text-sm text-muted-foreground">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span>Real-time</span>
          </div>
        </div>
      </div>

      {/* Portfolio Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <motion.div
          whileHover={{ scale: 1.02 }}
          className="bg-card border border-border rounded-xl p-6 shadow-sm"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-muted-foreground">Total Value</h3>
            <DollarSign className="w-5 h-5 text-muted-foreground" />
          </div>
          <p className="text-2xl font-bold text-foreground">
            ${portfolioStats.totalValue.toLocaleString()}
          </p>
          <div className={`flex items-center mt-2 text-sm ${getPnLColor(portfolioStats.totalPnL)}`}>
            <TrendingUp className="w-4 h-4 mr-1" />
            <span>{portfolioStats.totalPnLPercent.toFixed(2)}% All Time</span>
          </div>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className="bg-card border border-border rounded-xl p-6 shadow-sm"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-muted-foreground">Day Change</h3>
            <Activity className="w-5 h-5 text-muted-foreground" />
          </div>
          <p className="text-2xl font-bold text-foreground">
            +${portfolioStats.dayChange.toLocaleString()}
          </p>
          <div className={`flex items-center mt-2 text-sm ${getPnLColor(portfolioStats.dayChange)}`}>
            <TrendingUp className="w-4 h-4 mr-1" />
            <span>{portfolioStats.dayChangePercent.toFixed(2)}% Today</span>
          </div>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className="bg-card border border-border rounded-xl p-6 shadow-sm"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-muted-foreground">Cash Available</h3>
            <BarChart3 className="w-5 h-5 text-muted-foreground" />
          </div>
          <p className="text-2xl font-bold text-foreground">
            ${portfolioStats.cash.toLocaleString()}
          </p>
          <p className="text-sm text-muted-foreground mt-2">Ready to invest</p>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className="bg-card border border-border rounded-xl p-6 shadow-sm"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-muted-foreground">Total Equity</h3>
            <PieChart className="w-5 h-5 text-muted-foreground" />
          </div>
          <p className="text-2xl font-bold text-foreground">
            ${portfolioStats.totalEquity.toLocaleString()}
          </p>
          <p className="text-sm text-muted-foreground mt-2">Cash + Investments</p>
        </motion.div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Portfolio Performance */}
        <div className="lg:col-span-2 bg-card border border-border rounded-xl p-6">
          <h3 className="text-lg font-semibold text-foreground mb-6">Portfolio Performance</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis 
                dataKey="date" 
                stroke="#6b7280"
                fontSize={12}
                tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              />
              <YAxis 
                stroke="#6b7280"
                fontSize={12}
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#f1f5f9'
                }}
                formatter={(value: any) => [`$${value.toLocaleString()}`, 'Portfolio Value']}
                labelFormatter={(label) => new Date(label).toLocaleDateString()}
              />
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke="#3b82f6" 
                strokeWidth={2}
                dot={{ fill: '#3b82f6', r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Sector Allocation */}
        <div className="bg-card border border-border rounded-xl p-6">
          <h3 className="text-lg font-semibold text-foreground mb-6">Sector Allocation</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={sectorAllocation}
                cx="50%"
                cy="50%"
                innerRadius={40}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
              >
                {sectorAllocation.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#f1f5f9'
                }}
                formatter={(value: any) => [`$${value.toLocaleString()}`, 'Value']}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 space-y-2">
            {sectorAllocation.map((sector) => (
              <div key={sector.name} className="flex items-center justify-between text-sm">
                <div className="flex items-center space-x-2">
                  <div 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: sector.color }}
                  />
                  <span className="text-muted-foreground">{sector.name}</span>
                </div>
                <div className="text-right">
                  <span className="text-foreground font-medium">{sector.percentage}%</span>
                  <p className="text-xs text-muted-foreground">${sector.value.toLocaleString()}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Positions Table */}
      <div className="bg-card border border-border rounded-xl overflow-hidden">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold text-foreground">Open Positions</h3>
          <p className="text-sm text-muted-foreground mt-1">{mockPositions.length} active positions</p>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/20">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Symbol
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Position
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Market Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  P&L
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Target / Stop
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Signal
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {mockPositions.map((position) => (
                <tr key={position.id} className="hover:bg-muted/10 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-semibold text-foreground">{position.symbol}</div>
                      <div className="text-sm text-muted-foreground">{position.company}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-foreground">
                      {position.quantity} shares
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Avg: ${position.avgCost.toFixed(2)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-semibold text-foreground">
                      ${position.marketValue.toLocaleString()}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      ${position.currentPrice.toFixed(2)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className={`text-sm font-semibold ${getPnLColor(position.unrealizedPnL)}`}>
                      {position.unrealizedPnL >= 0 ? '+' : ''}${position.unrealizedPnL.toLocaleString()}
                    </div>
                    <div className={`text-sm ${getPnLColor(position.unrealizedPnL)}`}>
                      {position.unrealizedPnLPercent >= 0 ? '+' : ''}{position.unrealizedPnLPercent.toFixed(2)}%
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2 text-sm">
                      <div className="flex items-center space-x-1">
                        <Target className="w-3 h-3 text-muted-foreground" />
                        <span className="text-foreground">${position.targetPrice.toFixed(2)}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <StopCircle className="w-3 h-3 text-muted-foreground" />
                        <span className="text-foreground">${position.stopLoss.toFixed(2)}</span>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getSignalColor(position.lastSignal)}`}>
                        {position.lastSignal}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {(position.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <button 
                      onClick={() => setSelectedPosition(selectedPosition === position.id ? null : position.id)}
                      className="text-blue-400 hover:text-blue-300 transition-colors"
                    >
                      {selectedPosition === position.id ? 'Hide' : 'Details'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Position Details Modal */}
      {selectedPosition && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedPosition(null)}
        >
          <motion.div
            initial={{ scale: 0.95 }}
            animate={{ scale: 1 }}
            className="bg-card border border-border rounded-xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Position details would go here */}
            <h3 className="text-lg font-semibold text-foreground mb-4">Position Details</h3>
            <p className="text-muted-foreground">Detailed position analysis and chart would be displayed here.</p>
          </motion.div>
        </motion.div>
      )}
    </div>
  )
}