import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Calendar, 
  TrendingUp, 
  TrendingDown, 
  Target,
  StopCircle,
  MessageSquare,
  Tag,
  Filter,
  Search,
  Plus,
  Edit2,
  Trash2,
  BarChart3
} from 'lucide-react'

interface Trade {
  id: string
  symbol: string
  company: string
  action: 'BUY' | 'SELL'
  quantity: number
  entryPrice: number
  exitPrice?: number
  entryDate: string
  exitDate?: string
  pnl?: number
  pnlPercent?: number
  rationale: string
  notes?: string
  tags: string[]
  confidence: number
  modelVersion: string
  sector: string
  holdingPeriod?: number
  rMultiple?: number
}

const mockTrades: Trade[] = [
  {
    id: '1',
    symbol: 'AAPL',
    company: 'Apple Inc.',
    action: 'BUY',
    quantity: 100,
    entryPrice: 170.50,
    exitPrice: 175.43,
    entryDate: '2024-10-15',
    exitDate: '2024-11-10',
    pnl: 493,
    pnlPercent: 2.89,
    rationale: 'Technical breakout above 200-day MA with strong volume confirmation',
    notes: 'Good execution, followed plan perfectly. Consider taking partial profits earlier next time.',
    tags: ['Swing Trade', 'Technical', 'Breakout'],
    confidence: 0.87,
    modelVersion: 'v2.1.3',
    sector: 'Technology',
    holdingPeriod: 26,
    rMultiple: 2.1
  },
  {
    id: '2',
    symbol: 'MSFT',
    company: 'Microsoft Corporation',
    action: 'BUY',
    quantity: 50,
    entryPrice: 365.20,
    exitPrice: 378.85,
    entryDate: '2024-10-20',
    exitDate: '2024-11-12',
    pnl: 682.50,
    pnlPercent: 3.74,
    rationale: 'Azure growth acceleration signals, cloud market expansion',
    notes: 'Strong fundamental play. Model confidence was spot on.',
    tags: ['Fundamental', 'Growth', 'Cloud'],
    confidence: 0.92,
    modelVersion: 'v2.1.3',
    sector: 'Technology',
    holdingPeriod: 23,
    rMultiple: 2.8
  },
  {
    id: '3',
    symbol: 'GOOGL',
    company: 'Alphabet Inc.',
    action: 'SELL',
    quantity: 75,
    entryPrice: 148.20,
    exitPrice: 142.56,
    entryDate: '2024-10-25',
    exitDate: '2024-11-08',
    pnl: -423,
    pnlPercent: -3.81,
    rationale: 'Regulatory concerns, antitrust investigations heating up',
    notes: 'Cut loss quickly as planned. Good risk management.',
    tags: ['Short', 'Regulatory Risk', 'Quick Exit'],
    confidence: 0.78,
    modelVersion: 'v2.1.2',
    sector: 'Technology',
    holdingPeriod: 14,
    rMultiple: -1.2
  },
  {
    id: '4',
    symbol: 'NVDA',
    company: 'NVIDIA Corporation',
    action: 'BUY',
    quantity: 25,
    entryPrice: 480.00,
    exitPrice: 495.22,
    entryDate: '2024-10-28',
    exitDate: '2024-11-11',
    pnl: 380.50,
    pnlPercent: 3.17,
    rationale: 'AI chip demand surge, data center revenue growth',
    notes: 'AI momentum continues. Should have taken larger position.',
    tags: ['AI', 'Semiconductor', 'Momentum'],
    confidence: 0.89,
    modelVersion: 'v2.1.3',
    sector: 'Technology',
    holdingPeriod: 14,
    rMultiple: 2.3
  },
]

const journalStats = {
  totalTrades: 47,
  winningTrades: 32,
  losingTrades: 15,
  winRate: 68.1,
  avgWin: 456.78,
  avgLoss: -234.56,
  profitFactor: 1.95,
  avgHoldingPeriod: 18.5,
  totalPnL: 12847.30
}

export default function JournalPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedTag, setSelectedTag] = useState('All')
  const [selectedSymbol, setSelectedSymbol] = useState('All')
  const [showAddTrade, setShowAddTrade] = useState(false)
  const [selectedTrade, setSelectedTrade] = useState<Trade | null>(null)

  const allTags = ['All', ...Array.from(new Set(mockTrades.flatMap(trade => trade.tags)))]
  const allSymbols = ['All', ...Array.from(new Set(mockTrades.map(trade => trade.symbol)))]

  const filteredTrades = mockTrades.filter(trade => {
    const matchesSearch = trade.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         trade.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         trade.rationale.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         trade.notes?.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesTag = selectedTag === 'All' || trade.tags.includes(selectedTag)
    const matchesSymbol = selectedSymbol === 'All' || trade.symbol === selectedSymbol
    
    return matchesSearch && matchesTag && matchesSymbol
  })

  const getPnLColor = (pnl: number) => {
    return pnl >= 0 ? 'text-gain' : 'text-loss'
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Trade Journal</h1>
          <p className="text-muted-foreground mt-1">Analyze your trading performance and patterns</p>
        </div>
        <button
          onClick={() => setShowAddTrade(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Add Trade</span>
        </button>
      </div>

      {/* Journal Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <motion.div
          whileHover={{ scale: 1.02 }}
          className="bg-card border border-border rounded-xl p-6 shadow-sm"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-muted-foreground">Total P&L</h3>
            <TrendingUp className="w-5 h-5 text-muted-foreground" />
          </div>
          <p className="text-2xl font-bold text-foreground">
            +${journalStats.totalPnL.toLocaleString()}
          </p>
          <p className="text-sm text-muted-foreground mt-2">
            {journalStats.totalTrades} total trades
          </p>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className="bg-card border border-border rounded-xl p-6 shadow-sm"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-muted-foreground">Win Rate</h3>
            <Target className="w-5 h-5 text-muted-foreground" />
          </div>
          <p className="text-2xl font-bold text-foreground">
            {journalStats.winRate.toFixed(1)}%
          </p>
          <p className="text-sm text-muted-foreground mt-2">
            {journalStats.winningTrades}W / {journalStats.losingTrades}L
          </p>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className="bg-card border border-border rounded-xl p-6 shadow-sm"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-muted-foreground">Profit Factor</h3>
            <BarChart3 className="w-5 h-5 text-muted-foreground" />
          </div>
          <p className="text-2xl font-bold text-foreground">
            {journalStats.profitFactor.toFixed(2)}
          </p>
          <p className="text-sm text-muted-foreground mt-2">
            Avg win / Avg loss
          </p>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className="bg-card border border-border rounded-xl p-6 shadow-sm"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-muted-foreground">Avg Hold Time</h3>
            <Calendar className="w-5 h-5 text-muted-foreground" />
          </div>
          <p className="text-2xl font-bold text-foreground">
            {journalStats.avgHoldingPeriod.toFixed(1)}d
          </p>
          <p className="text-sm text-muted-foreground mt-2">
            Average holding period
          </p>
        </motion.div>
      </div>

      {/* Search and Filters */}
      <div className="bg-card border border-border rounded-xl p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0 lg:space-x-4">
          <div className="relative flex-1 lg:max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search trades..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-muted/20 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div className="flex items-center space-x-3">
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="px-3 py-2 bg-muted/20 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {allSymbols.map(symbol => (
                <option key={symbol} value={symbol}>{symbol}</option>
              ))}
            </select>

            <select
              value={selectedTag}
              onChange={(e) => setSelectedTag(e.target.value)}
              className="px-3 py-2 bg-muted/20 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {allTags.map(tag => (
                <option key={tag} value={tag}>{tag}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Trade List */}
      <div className="space-y-4">
        {filteredTrades.map((trade, index) => (
          <motion.div
            key={trade.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-card border border-border rounded-xl overflow-hidden hover:border-blue-500/30 transition-colors"
          >
            <div className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-lg font-bold text-foreground">{trade.symbol}</h3>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      trade.action === 'BUY' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                    }`}>
                      {trade.action}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      {trade.quantity} shares
                    </span>
                  </div>
                  <p className="text-muted-foreground mb-3">{trade.company}</p>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div>
                      <p className="text-xs text-muted-foreground">Entry Price</p>
                      <p className="text-sm font-semibold text-foreground">${trade.entryPrice.toFixed(2)}</p>
                    </div>
                    {trade.exitPrice && (
                      <div>
                        <p className="text-xs text-muted-foreground">Exit Price</p>
                        <p className="text-sm font-semibold text-foreground">${trade.exitPrice.toFixed(2)}</p>
                      </div>
                    )}
                    {trade.pnl && (
                      <div>
                        <p className="text-xs text-muted-foreground">P&L</p>
                        <p className={`text-sm font-semibold ${getPnLColor(trade.pnl)}`}>
                          {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toLocaleString()}
                        </p>
                      </div>
                    )}
                    {trade.rMultiple && (
                      <div>
                        <p className="text-xs text-muted-foreground">R-Multiple</p>
                        <p className="text-sm font-semibold text-foreground">
                          {trade.rMultiple.toFixed(1)}R
                        </p>
                      </div>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-2 mb-3">
                    {trade.tags.map((tag, tagIndex) => (
                      <span
                        key={tagIndex}
                        className="inline-flex items-center space-x-1 px-2 py-1 bg-muted/20 text-muted-foreground text-xs rounded-md"
                      >
                        <Tag className="w-3 h-3" />
                        <span>{tag}</span>
                      </span>
                    ))}
                  </div>

                  <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                    <div className="flex items-center space-x-1">
                      <Calendar className="w-4 h-4" />
                      <span>{formatDate(trade.entryDate)}</span>
                      {trade.exitDate && (
                        <>
                          <span>-</span>
                          <span>{formatDate(trade.exitDate)}</span>
                          <span>({trade.holdingPeriod}d)</span>
                        </>
                      )}
                    </div>
                    <div className="flex items-center space-x-1">
                      <MessageSquare className="w-4 h-4" />
                      <span>Model: {trade.modelVersion}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Target className="w-4 h-4" />
                      <span>{(trade.confidence * 100).toFixed(0)}% confidence</span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-col items-end space-y-2">
                  {trade.pnl && (
                    <div className={`text-lg font-bold ${getPnLColor(trade.pnl)}`}>
                      {trade.pnlPercent && `${trade.pnlPercent >= 0 ? '+' : ''}${trade.pnlPercent.toFixed(2)}%`}
                    </div>
                  )}
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setSelectedTrade(trade)}
                      className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted/20 rounded-lg transition-colors"
                    >
                      <MessageSquare className="w-4 h-4" />
                    </button>
                    <button className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted/20 rounded-lg transition-colors">
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button className="p-2 text-muted-foreground hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>

              {trade.rationale && (
                <div className="mt-4 pt-4 border-t border-border">
                  <h4 className="text-sm font-semibold text-foreground mb-2">Trade Rationale</h4>
                  <p className="text-sm text-muted-foreground">{trade.rationale}</p>
                </div>
              )}
            </div>
          </motion.div>
        ))}

        {filteredTrades.length === 0 && (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-muted/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <Search className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">No trades found</h3>
            <p className="text-muted-foreground">Try adjusting your search criteria or filters</p>
          </div>
        )}
      </div>

      {/* Trade Details Modal */}
      {selectedTrade && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedTrade(null)}
        >
          <motion.div
            initial={{ scale: 0.95 }}
            animate={{ scale: 1 }}
            className="bg-card border border-border rounded-xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-foreground">Trade Notes</h3>
              <button
                onClick={() => setSelectedTrade(null)}
                className="p-2 hover:bg-muted/20 rounded-lg transition-colors"
              >
                <Plus className="w-5 h-5 transform rotate-45" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-2">
                  Trade Notes
                </label>
                <textarea
                  defaultValue={selectedTrade.notes || 'Add your notes about this trade...'}
                  className="w-full h-32 px-3 py-2 bg-muted/20 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  placeholder="What did you learn from this trade? What would you do differently?"
                />
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setSelectedTrade(null)}
                  className="px-4 py-2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => setSelectedTrade(null)}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  Save Notes
                </button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}

      {/* Add Trade Modal */}
      {showAddTrade && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50"
          onClick={() => setShowAddTrade(false)}
        >
          <motion.div
            initial={{ scale: 0.95 }}
            animate={{ scale: 1 }}
            className="bg-card border border-border rounded-xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-foreground">Add New Trade</h3>
              <button
                onClick={() => setShowAddTrade(false)}
                className="p-2 hover:bg-muted/20 rounded-lg transition-colors"
              >
                <Plus className="w-5 h-5 transform rotate-45" />
              </button>
            </div>
            
            <div className="space-y-4">
              <p className="text-muted-foreground">Trade entry form would be implemented here.</p>
            </div>
          </motion.div>
        </motion.div>
      )}
    </div>
  )
}