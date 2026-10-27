import React from 'react'
import type { AppProps } from 'next/app'
import { CreditApplicationProvider } from '@/context/CreditApplicationContext'
import { ThemeProvider } from '@/context/ThemeContext'
import '../styles/globals.css'

export default function App({ Component, pageProps }: AppProps) {
  return (
    <ThemeProvider>
      <CreditApplicationProvider>
        <Component {...pageProps} />
      </CreditApplicationProvider>
    </ThemeProvider>
  )
}
