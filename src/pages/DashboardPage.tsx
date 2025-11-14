import React from 'react'
import { motion } from 'framer-motion'
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Activity,
  Target,
  AlertCircle
} from 'lucide-react'
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

// Mock data for charts
const equityData = [
  { date: '2024-01', value: 100000 },
  { date: '2024-02', value: 105000 },
  { date: '2024-03', value: 108000 },
  { date: '2024-04', value: 112000 },
  { date: '2024-05', value: 109000 },
  { date: '2024-06', value: 115000 },
  { date: '2024-07', value: 118000 },
  { date: '2024-08', value: 122000 },
  { date: '2024-09', value: 125000 },
  { date: '2024-10', value: 128000 },
  { date: '2024-11', value: 132000 },
]

const performanceData = [
  { month: 'Jan', pnl: 5000 },
  { month: 'Feb', pnl: 3000 },
  { month: 'Mar', pnl: 4000 },
  { month: 'Apr', pnl: -2000 },
  { month: 'May', pnl: 6000 },
  { month: 'Jun', pnl: 3000 },
  { month: 'Jul', pnl: 4000 },
  { month: 'Aug', pnl: 5000 },
  { month: 'Sep', pnl: 3000 },
  { month: 'Oct', pnl: 4000 },
  { month: 'Nov', pnl: 3000 },
]

const sectorData = [
  { name: 'Technology', value: 35, color: '#3b82f6' },
  { name: 'Healthcare', value: 25, color: '#10b981' },
  { name: 'Finance', value: 20, color: '#f59e0b' },
  { name: 'Energy', value: 12, color: '#ef4444' },
  { name: 'Others', value: 8, color: '#6b7280' },
]

const recentSignals = [
  { symbol: 'AAPL', action: 'BUY', confidence: 0.87, price: 175.43, time: '2 hours ago' },
  { symbol: 'MSFT', action: 'SELL', confidence: 0.92, price: 378.85, time: '4 hours ago' },
  { symbol: 'GOOGL', action: 'BUY', confidence: 0.78, price: 142.56, time: '6 hours ago' },
  { symbol: 'TSLA', action: 'HOLD', confidence: 0.65, price: 248.42, time: '8 hours ago' },
]

const MetricCard = ({ title, value, change, icon: Icon, trend }: any) => (
  <motion.div
    whileHover={{ scale: 1.02 }}
    className="bg-card border border-border rounded-xl p-6 shadow-sm"
  >
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-muted-foreground">{title}</p>
        <p className="text-2xl font-bold text-foreground mt-1">{value}</p>
        {change && (
          <div className={`flex items-center mt-2 text-sm ${
            trend === 'up' ? 'text-gain' : 'text-loss'
          }`}>
            {trend === 'up' ? <TrendingUp className="w-4 h-4 mr-1" /> : <TrendingDown className="w-4 h-4 mr-1" />}
            <span>{change}</span>
          </div>
        )}
      </div>
      <div className="w-12 h-12 bg-muted/20 rounded-lg flex items-center justify-center">
        <Icon className="w-6 h-6 text-muted-foreground" />
      </div>
    </div>
  </motion.div>
)

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
          <p className="text-muted-foreground mt-1">Welcome back to your trading terminal</p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 text-sm text-muted-foreground">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span>Live</span>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Portfolio Value"
          value="$132,000"
          change="+32.0%"
          icon={DollarSign}
          trend="up"
        />
        <MetricCard
          title="Today's P&L"
          value="+$3,000"
          change="+2.3%"
          icon={TrendingUp}
          trend="up"
        />
        <MetricCard
          title="Sharpe Ratio"
          value="1.85"
          change="+0.12"
          icon={Target}
          trend="up"
        />
        <MetricCard
          title="Win Rate"
          value="68.5%"
          change="-2.1%"
          icon={Activity}
          trend="down"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Equity Curve */}
        <div className="lg:col-span-2 bg-card border border-border rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-foreground">Equity Curve</h3>
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <div className="w-3 h-3 bg-blue-500 rounded-full" />
              <span>Portfolio Value</span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={equityData}>
              <defs>
                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis 
                dataKey="date" 
                stroke="#6b7280"
                fontSize={12}
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
              />
              <Area 
                type="monotone" 
                dataKey="value" 
                stroke="#3b82f6" 
                fillOpacity={1} 
                fill="url(#colorValue)" 
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Sector Allocation */}
        <div className="bg-card border border-border rounded-xl p-6">
          <h3 className="text-lg font-semibold text-foreground mb-6">Sector Allocation</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={sectorData}
                cx="50%"
                cy="50%"
                innerRadius={40}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
              >
                {sectorData.map((entry, index) => (
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
                formatter={(value: any) => [`${value}%`, 'Allocation']}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 space-y-2">
            {sectorData.map((sector) => (
              <div key={sector.name} className="flex items-center justify-between text-sm">
                <div className="flex items-center space-x-2">
                  <div 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: sector.color }}
                  />
                  <span className="text-muted-foreground">{sector.name}</span>
                </div>
                <span className="text-foreground font-medium">{sector.value}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Performance Chart and Recent Signals */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly Performance */}
        <div className="bg-card border border-border rounded-xl p-6">
          <h3 className="text-lg font-semibold text-foreground mb-6">Monthly P&L</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis 
                dataKey="month" 
                stroke="#6b7280"
                fontSize={12}
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
                formatter={(value: any) => [`$${value.toLocaleString()}`, 'P&L']}
              />
              <Bar 
                dataKey="pnl" 
                fill={(entry: any) => entry.pnl >= 0 ? '#10b981' : '#ef4444'}
              >
                {performanceData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.pnl >= 0 ? '#10b981' : '#ef4444'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Recent Signals */}
        <div className="bg-card border border-border rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-foreground">Recent Signals</h3>
            <button className="text-sm text-blue-400 hover:text-blue-300 transition-colors">
              View all
            </button>
          </div>
          <div className="space-y-4">
            {recentSignals.map((signal, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="flex items-center justify-between p-3 bg-muted/20 rounded-lg"
              >
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-semibold text-foreground">{signal.symbol}</span>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      signal.action === 'BUY' ? 'bg-green-500/20 text-green-400' :
                      signal.action === 'SELL' ? 'bg-red-500/20 text-red-400' :
                      'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {signal.action}
                    </span>
                  </div>
                  <div className="flex items-center space-x-4 mt-1">
                    <span className="text-sm text-muted-foreground">${signal.price}</span>
                    <span className="text-sm text-muted-foreground">
                      {(signal.confidence * 100).toFixed(0)}% conf
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs text-muted-foreground">{signal.time}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-card border border-border rounded-xl p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">Quick Actions</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button className="p-4 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/20 rounded-lg text-blue-400 hover:text-blue-300 transition-all duration-200 text-center">
            <TrendingUp className="w-6 h-6 mx-auto mb-2" />
            <span className="text-sm font-medium">View Signals</span>
          </button>
          <button className="p-4 bg-green-500/10 hover:bg-green-500/20 border border-green-500/20 rounded-lg text-green-400 hover:text-green-300 transition-all duration-200 text-center">
            <Briefcase className="w-6 h-6 mx-auto mb-2" />
            <span className="text-sm font-medium">Portfolio</span>
          </button>
          <button className="p-4 bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/20 rounded-lg text-purple-400 hover:text-purple-300 transition-all duration-200 text-center">
            <Brain className="w-6 h-6 mx-auto mb-2" />
            <span className="text-sm font-medium">Model Insights</span>
          </button>
          <button className="p-4 bg-orange-500/10 hover:bg-orange-500/20 border border-orange-500/20 rounded-lg text-orange-400 hover:text-orange-300 transition-all duration-200 text-center">
            <AlertCircle className="w-6 h-6 mx-auto mb-2" />
            <span className="text-sm font-medium">Risk Alert</span>
          </button>
        </div>
      </div>
    </div>
  )
}