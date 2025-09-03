import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { recipeService } from '../services/api';
import { Recipe } from '../types';

const Dashboard: React.FC = () => {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchRecipes();
  }, []);

  const fetchRecipes = async () => {
    try {
      const data = await recipeService.getAll();
      setRecipes(data);
    } catch (err) {
      setError('Failed to load recipes');
    } finally {
      setLoading(false);
    }
  };

  const getHealthColor = (rating?: number) => {
    if (!rating) return 'text-gray-500';
    if (rating >= 7) return 'text-green-600';
    if (rating >= 4) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getRatingStars = (rating?: number) => {
    if (!rating) return '☆☆☆☆☆';
    const filled = '★'.repeat(Math.round(rating));
    const empty = '☆'.repeat(5 - Math.round(rating));
    return filled + empty;
  };

  return (
    <div>
      <Navbar />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">My Recipes</h1>
          <Link
            to="/recipes/new"
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md font-medium"
          >
            Add New Recipe
          </Link>
        </div>

        {loading && (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
          </div>
        )}

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {!loading && recipes.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500 mb-4">No recipes yet</p>
            <Link
              to="/recipes/new"
              className="text-green-600 hover:text-green-700 font-medium"
            >
              Add your first recipe
            </Link>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {recipes.map((recipe) => (
            <Link
              key={recipe.id}
              to={`/recipes/${recipe.id}`}
              className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-6"
            >
              <h3 className="text-xl font-semibold mb-2">{recipe.title}</h3>
              
              <div className="space-y-2 text-sm">
                {recipe.cuisine_type && (
                  <p className="text-gray-600">Cuisine: {recipe.cuisine_type}</p>
                )}
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Calories:</span>
                  <span className="font-medium">{recipe.calories || 'N/A'}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Health Rating:</span>
                  <span className={`font-medium ${getHealthColor(recipe.health_rating)}`}>
                    {recipe.health_rating ? `${recipe.health_rating}/10` : 'N/A'}
                  </span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Taste:</span>
                  <span className="text-yellow-500">
                    {getRatingStars(recipe.taste_rating)}
                  </span>
                </div>
                
                {recipe.dietary_tags && recipe.dietary_tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {recipe.dietary_tags.map((tag, index) => (
                      <span
                        key={index}
                        className="bg-gray-200 text-gray-700 px-2 py-1 rounded-md text-xs"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;