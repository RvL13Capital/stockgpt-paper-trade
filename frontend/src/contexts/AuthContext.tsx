import React, { createContext, useContext, useState, useEffect } from 'react'

interface AuthContextType {
  isAuthenticated: boolean
  login: (email: string, otp: string) => Promise<boolean>
  logout: () => void
  user: { email: string } | null
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState<{ email: string } | null>(null)

  useEffect(() => {
    // Check if user is already authenticated
    const token = localStorage.getItem('auth_token')
    const userEmail = localStorage.getItem('user_email')
    
    if (token && userEmail) {
      setIsAuthenticated(true)
      setUser({ email: userEmail })
    }
  }, [])

  const login = async (email: string, otp: string): Promise<boolean> => {
    // Simulate OTP validation - in real app, this would call the backend
    if (otp.length === 4 && /\d{4}/.test(otp)) {
      // Mock successful login
      const mockToken = btoa(`${email}:${Date.now()}`)
      localStorage.setItem('auth_token', mockToken)
      localStorage.setItem('user_email', email)
      
      setIsAuthenticated(true)
      setUser({ email })
      return true
    }
    
    return false
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_email')
    setIsAuthenticated(false)
    setUser(null)
  }

  const value = {
    isAuthenticated,
    login,
    logout,
    user,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}