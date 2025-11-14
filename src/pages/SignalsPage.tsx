import React, { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import { 
  Search, 
  Filter, 
  TrendingUp,n  TrendingDown,
  Target,
  Clock,
  Percent,
  ChevronDown,
  ChevronUp,
  ExternalLink
} from 'lucide-react'

interface Signal {
  id: string
  symbol: string
  company: string
  action: 'BUY' | 'SELL' | 'HOLD'
  confidence: number
  entryPrice: number
  targetPrice: number
  stopLoss: number
  sector: string
  timeGenerated: string
  rationale: string
  modelVersion: string
  expectedReturn: number
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH'
}

const mockSignals: Signal[] = [
  {
    id: '1',
    symbol: 'AAPL',
    company: 'Apple Inc.',
    action: 'BUY',
    confidence: 0.87,
    entryPrice: 175.43,
    targetPrice: 185.00,
    stopLoss: 170.00,
    sector: 'Technology',
    timeGenerated: '2024-11-13T10:30:00Z',
    rationale: 'Strong momentum in AI services revenue growth, technical breakout above 200-day MA',
    modelVersion: 'v2.1.3',
    expectedReturn: 5.45,
    riskLevel: 'MEDIUM'
  },
  {
    id: '2',
    symbol: 'MSFT',
    company: 'Microsoft Corporation',
    action: 'BUY',
    confidence: 0.92,
    entryPrice: 378.85,
    targetPrice: 395.00,
    stopLoss: 365.00,
    sector: 'Technology',
    timeGenerated: '2024-11-13T09:15:00Z',
    rationale: 'Azure growth acceleration, cloud market share expansion, strong fundamentals',
    modelVersion: 'v2.1.3',
    expectedReturn: 4.26,
    riskLevel: 'LOW'
  },
  {
    id: '3',
    symbol: 'GOOGL',
    company: 'Alphabet Inc.',
    action: 'SELL',
    confidence: 0.78,
    entryPrice: 142.56,
    targetPrice: 135.00,
    stopLoss: 148.00,
    sector: 'Technology',
    timeGenerated: '2024-11-13T08:45:00Z',
    rationale: 'Regulatory pressure increasing, search market share concerns, overvaluation signals',
    modelVersion: 'v2.1.2',
    expectedReturn: 5.31,
    riskLevel: 'MEDIUM'
  },
  {
    id: '4',
    symbol: 'TSLA',
    company: 'Tesla Inc.',
    action: 'HOLD',
    confidence: 0.65,
    entryPrice: 248.42,
    targetPrice: 265.00,
    stopLoss: 235.00,
    sector: 'Automotive',
    timeGenerated: '2024-11-13T07:30:00Z',
    rationale: 'Mixed signals on EV demand, wait for clearer trend confirmation',
    modelVersion: 'v2.1.3',
    expectedReturn: 6.67,
    riskLevel: 'HIGH'
  },
  {
    id: '5',
    symbol: 'JPM',
    company: 'JPMorgan Chase & Co.',
    action: 'BUY',
    confidence: 0.84,
    entryPrice: 168.23,
    targetPrice: 178.00,
    stopLoss: 162.00,
    sector: 'Finance',
    timeGenerated: '2024-11-13T06:20:00Z',
    rationale: 'Interest rate environment favorable, strong Q3 earnings beat',
    modelVersion: 'v2.1.2',
    expectedReturn: 5.81,
    riskLevel: 'LOW'
  },
  {
    id: '6',
    symbol: 'NVDA',
    company: 'NVIDIA Corporation',
    action: 'BUY',
    confidence: 0.89,
    entryPrice: 495.22,
    targetPrice: 520.00,
    stopLoss: 475.00,
    sector: 'Technology',
    timeGenerated: '2024-11-13T05:10:00Z',
    rationale: 'AI chip demand surge, data center revenue growth, technical strength',
    modelVersion: 'v2.1.3',
    expectedReturn: 5.00,
    riskLevel: 'MEDIUM'
  },
]

const sectors = ['All', 'Technology', 'Finance', 'Healthcare', 'Energy', 'Automotive']
const actions = ['All', 'BUY', 'SELL', 'HOLD']
const riskLevels = ['All', 'LOW', 'MEDIUM', 'HIGH']

export default function SignalsPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedSector, setSelectedSector] = useState('All')
  const [selectedAction, setSelectedAction] = useState('All')
  const [selectedRisk, setSelectedRisk] = useState('All')
  const [expandedSignal, setExpandedSignal] = useState<string | null>(null)
  const [showFilters, setShowFilters] = useState(false)

  const filteredSignals = useMemo(() => {
    return mockSignals.filter(signal => {
      const matchesSearch = signal.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          signal.company.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesSector = selectedSector === 'All' || signal.sector === selectedSector
      const matchesAction = selectedAction === 'All' || signal.action === selectedAction
      const matchesRisk = selectedRisk === 'All' || signal.riskLevel === selectedRisk
      
      return matchesSearch && matchesSector && matchesAction && matchesRisk
    })
  }, [searchTerm, selectedSector, selectedAction, selectedRisk])

  const getActionColor = (action: string) => {
    switch (action) {
      case 'BUY': return 'text-green-400 bg-green-500/20'
      case 'SELL': return 'text-red-400 bg-red-500/20'
      case 'HOLD': return 'text-yellow-400 bg-yellow-500/20'
      default: return 'text-gray-400 bg-gray-500/20'
    }
  }

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'LOW': return 'text-green-400'
      case 'MEDIUM': return 'text-yellow-400'
      case 'HIGH': return 'text-red-400'
      default: return 'text-gray-400'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Trading Signals</h1>
          <p className="text-muted-foreground mt-1">AI-generated signals with confidence scores</p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 text-sm text-muted-foreground">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span>Live Updates</span>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-card border border-border rounded-xl p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          <div className="relative flex-1 lg:max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search by symbol or company..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-muted/20 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center space-x-2 px-4 py-2 bg-muted/20 hover:bg-muted/30 border border-border rounded-lg transition-colors lg:hidden"
          >
            <Filter className="w-4 h-4" />
            <span>Filters</span>
            {showFilters ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          <div className={`flex flex-col lg:flex-row lg:items-center space-y-4 lg:space-y-0 lg:space-x-3 ${showFilters ? 'block' : 'hidden lg:flex'}`}>
            <select
              value={selectedSector}
              onChange={(e) => setSelectedSector(e.target.value)}
              className="px-3 py-2 bg-muted/20 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {sectors.map(sector => (
                <option key={sector} value={sector}>{sector}</option>
              ))}
            </select>

            <select
              value={selectedAction}
              onChange={(e) => setSelectedAction(e.target.value)}
              className="px-3 py-2 bg-muted/20 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {actions.map(action => (
                <option key={action} value={action}>{action}</option>
              ))}
            </select>

            <select
              value={selectedRisk}
              onChange={(e) => setSelectedRisk(e.target.value)}
              className="px-3 py-2 bg-muted/20 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {riskLevels.map(risk => (
                <option key={risk} value={risk}>{risk}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Signals List */}
      <div className="space-y-4">
        {filteredSignals.map((signal) => (
          <motion.div
            key={signal.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-card border border-border rounded-xl overflow-hidden"
          >
            <div className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-lg font-bold text-foreground">{signal.symbol}</h3>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getActionColor(signal.action)}`}>
                      {signal.action}
                    </span>
                    <span className={`text-sm font-medium ${getRiskColor(signal.riskLevel)}`}>
                      {signal.riskLevel} RISK
                    </span>
                  </div>
                  <p className="text-muted-foreground mb-3">{signal.company}</p>
                  <div className="flex items-center space-x-6 text-sm">
                    <div className="flex items-center space-x-2">
                      <Target className="w-4 h-4 text-muted-foreground" />
                      <span className="text-muted-foreground">Entry:</span>
                      <span className="text-foreground font-medium">${signal.entryPrice}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <TrendingUp className="w-4 h-4 text-muted-foreground" />
                      <span className="text-muted-foreground">Target:</span>
                      <span className="text-foreground font-medium">${signal.targetPrice}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <TrendingDown className="w-4 h-4 text-muted-foreground" />
                      <span className="text-muted-foreground">Stop:</span>
                      <span className="text-foreground font-medium">${signal.stopLoss}</span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-col items-end space-y-3">
                  <div className="text-right">
                    <div className="flex items-center space-x-2">
                      <Percent className="w-4 h-4 text-muted-foreground" />
                      <span className="text-lg font-bold text-foreground">
                        {(signal.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">Confidence</p>
                  </div>
                  <button
                    onClick={() => setExpandedSignal(expandedSignal === signal.id ? null : signal.id)}
                    className="flex items-center space-x-1 text-sm text-blue-400 hover:text-blue-300 transition-colors"
                  >
                    <span>Details</span>
                    {expandedSignal === signal.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            </div>

            {/* Expanded Details */}
            {expandedSignal === signal.id && (
              <motion.div
                initial={{ height: 0 }}
                animate={{ height: 'auto' }}
                exit={{ height: 0 }}
                className="border-t border-border bg-muted/10"
              >
                <div className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="text-sm font-semibold text-foreground mb-3">Signal Details</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Sector:</span>
                          <span className="text-foreground">{signal.sector}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Expected Return:</span>
                          <span className="text-foreground">{signal.expectedReturn.toFixed(2)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Model Version:</span>
                          <span className="text-foreground">{signal.modelVersion}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Generated:</span>
                          <span className="text-foreground">
                            {new Date(signal.timeGenerated).toLocaleString()}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-foreground mb-3">AI Rationale</h4>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        {signal.rationale}
                      </p>
                      <button className="mt-3 flex items-center space-x-1 text-sm text-blue-400 hover:text-blue-300 transition-colors">
                        <span>View SHAP Analysis</span>
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </motion.div>
        ))}

        {filteredSignals.length === 0 && (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-muted/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <Search className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">No signals found</h3>
            <p className="text-muted-foreground">Try adjusting your search criteria or filters</p>
          </div>
        )}
      </div>
    </div>
  )
}