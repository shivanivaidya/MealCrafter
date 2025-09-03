# MealCrafter

A comprehensive meal planning application with recipe management, nutrition calculation, and health rating features.

## Features

- **Recipe Input**: Add recipes as free-form text, which are automatically parsed
- **Nutrition Calculation**: Automatic calorie calculation with ±50 calories accuracy
- **Health Rating**: Rates recipes 1-10 based on ingredients, cooking methods, and nutritional content
- **User Ratings**: Rate recipes 1-5 stars for taste
- **Smart Search**: Search by ingredients, cuisine type, dietary restrictions, health ratings, and taste ratings
- **Vector Database**: Efficient recipe storage and similarity search using ChromaDB
- **User Authentication**: Secure username/password authentication with JWT tokens

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.9+)
- **Databases**: 
  - PostgreSQL for structured data
  - ChromaDB for vector storage
- **Authentication**: JWT-based authentication
- **Nutrition API**: Spoonacular API (free tier)

### Frontend
- **Framework**: React with TypeScript
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Routing**: React Router

## Prerequisites

- Python 3.9 or 3.10
- Node.js 16+
- Docker and Docker Compose
- Spoonacular API key (free tier available)

## Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd MealCrafter
```

### 2. Set up the backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from example
cp .env.example .env
```

Edit the `.env` file and add your configurations:
- Add your Spoonacular API key
- Update database credentials if needed
- Generate a secure SECRET_KEY for JWT

### 3. Set up the frontend

```bash
cd ../frontend
npm install
```

### 4. Start the database

```bash
# From project root
docker-compose up -d
```

This will start PostgreSQL on port 5432.

### 5. Install concurrently for running both servers

```bash
# From project root
npm install
```

## Running the Application

### Development Mode (Both servers concurrently)

```bash
# From project root
npm run dev
```

This starts:
- Backend API server at http://localhost:8000
- Frontend React app at http://localhost:3000

### Run servers individually

Backend:
```bash
cd backend
python main.py
```

Frontend:
```bash
cd frontend
npm start
```

### Database Management

```bash
# Start database
npm run db:up

# Stop database
npm run db:down

# Reset database (delete all data)
npm run db:reset
```

## API Documentation

Once the backend is running, access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Usage Guide

### 1. Register/Login
- Navigate to http://localhost:3000
- Create a new account or login with existing credentials

### 2. Add a Recipe
- Click "Add Recipe" button
- Enter recipe as free-form text including:
  - Recipe title
  - Ingredients list
  - Cooking instructions
  - Optional: cuisine type, dietary tags, prep/cook time

Example recipe format:
```
Spaghetti Carbonara

Ingredients:
- 400g spaghetti
- 200g pancetta, diced
- 4 eggs
- 100g Parmesan cheese
- 2 cloves garlic
- Salt and pepper

Instructions:
1. Cook spaghetti according to package directions
2. Fry pancetta until crispy
3. Mix eggs with Parmesan
4. Combine hot pasta with pancetta
5. Add egg mixture and toss
6. Season and serve

Serves: 4
```

### 3. View Recipe Details
- Click on any recipe card to view:
  - Full ingredients and instructions
  - Nutrition information per serving
  - Health rating (1-10)
  - Your taste rating

### 4. Search Recipes
- Use the search page to filter by:
  - Text search
  - Specific ingredients
  - Cuisine type
  - Dietary restrictions
  - Minimum health/taste ratings
  - Maximum calories

### 5. Rate Recipes
- On recipe detail page, click stars to rate taste (1-5)

## Configuration

### Environment Variables

Backend (`.env`):
```env
DATABASE_URL=postgresql://user:password@localhost:5432/mealcrafter
CHROMA_PERSIST_DIRECTORY=./chroma_db
SPOONACULAR_API_KEY=your_api_key_here
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
HOST=0.0.0.0
PORT=8000
```

### Spoonacular API

1. Sign up at https://spoonacular.com/food-api
2. Get your free API key (150 requests/day)
3. Add to `.env` file

## Health Rating Algorithm

The health rating (1-10) considers:
- **Ingredients**: Vegetables, whole grains, lean proteins increase score
- **Cooking Methods**: Steaming, grilling preferred over frying
- **Portion Control**: Appropriate serving sizes
- **Oil Content**: Excessive oil/butter reduces score
- **Added Sugars/Sodium**: High amounts reduce score
- **Nutritional Balance**: Fiber, protein content considered

## Error Handling

- **Invalid Recipe Format**: Returns specific feedback about unclear ingredients
- **API Failures**: Falls back to estimated nutrition calculations
- **Authentication Errors**: Automatic redirect to login
- **Network Issues**: User-friendly error messages

## Future Enhancements (Not yet implemented)

- Recipe URL import
- Video link processing (YouTube, Instagram)
- Photo OCR for handwritten recipes
- Advanced meal planning features
- Shopping list generation
- Social features (sharing, following)

## Troubleshooting

### Backend won't start
- Ensure Python 3.9+ is installed
- Check all dependencies are installed: `pip install -r requirements.txt`
- Verify PostgreSQL is running: `docker ps`
- Check `.env` file exists and is configured

### Frontend won't start
- Ensure Node.js 16+ is installed
- Run `npm install` in frontend directory
- Clear npm cache if needed: `npm cache clean --force`

### Database connection issues
- Verify Docker is running
- Check PostgreSQL container: `docker ps`
- Ensure DATABASE_URL in `.env` matches Docker configuration
- Try resetting database: `npm run db:reset`

### Recipe parsing errors
- Ensure recipe text includes clear sections for ingredients and instructions
- Use standard measurements (cups, tablespoons, grams, etc.)
- Include "Ingredients:" and "Instructions:" headers for best results

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details