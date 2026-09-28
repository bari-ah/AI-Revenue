# AI Revenue Optimization OS

AI-driven revenue optimization dashboard for hospitality businesses.

## 🚀 Deployment

### Deploy to Vercel

1. **Connect your GitHub repository**
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Select this repository

2. **Set Environment Variables**
   - In Vercel Dashboard → Settings → Environment Variables
   - Add: `NEXT_PUBLIC_API_URL` = `https://your-backend-api.com`
   - Replace with your actual backend API URL

3. **Deploy**
   - Click "Deploy"
   - Your site will be live at `https://your-project.vercel.app`

## 🔧 Configuration

### Local Development
```bash
# Frontend runs on http://localhost:3000 (Vercel default)
# Set backend API via environment variable:
export NEXT_PUBLIC_API_URL=http://localhost:3001
```

### Files
- `index.html` - Main UI (Tailwind CSS)
- `script.js` - Frontend logic
- `config.js` - API configuration
- `vercel.json` - Vercel deployment settings

## 📊 Features

- **Real-time Analysis** - Submit business metrics for AI analysis
- **Revenue Insights** - Get actionable revenue optimization recommendations
- **Dynamic Pricing** - Understand occupancy and rate optimization opportunities
- **Responsive Design** - Works on mobile, tablet, and desktop

## 🔌 API Integration

The application sends POST requests to: `{BACKEND_API_URL}/api/ai-core`

**Request Format:**
```json
{
  "hotel_name": "Hotel Name",
  "occupancy_rate": 72,
  "avg_daily_rate": 185,
  "rooms_count": 120
}
```

**Expected Response:**
```json
{
  "revenue_opportunity": 450000,
  "occupancy_improvement": 12.5,
  "recommendations": [
    "Implement dynamic pricing during peak seasons",
    "..."
  ]
}
```

## 🎨 Customization

Edit `config.js` to change:
- API endpoints
- Local development URLs
- Default configurations

## 📱 Demo Mode

If the backend API is unavailable, the app runs in demo mode showing sample analysis results.

## 🛠️ Troubleshooting

**"API unavailable" message:**
- Check your backend is running
- Verify `NEXT_PUBLIC_API_URL` environment variable
- Check CORS settings on backend

**Vercel deployment issues:**
- Ensure `vercel.json` is in root directory
- Check environment variables are set
- Review Vercel deployment logs

## 📄 License

MIT
