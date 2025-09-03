import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { recipeService } from '../services/api';

const RecipeForm: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedCuisine, setSelectedCuisine] = useState('');
  const [selectedDietaryTags, setSelectedDietaryTags] = useState<string[]>([]);
  const [formData, setFormData] = useState({
    title: '',
    raw_text: '',
    prep_time_minutes: '',
    cook_time_minutes: '',
    servings: '',
  });

  // Predefined cuisine types
  const cuisineTypes = [
    'Italian', 'Chinese', 'Indian', 'Mexican', 'Japanese', 
    'Thai', 'French', 'Mediterranean', 'American', 'Korean',
    'Vietnamese', 'Greek', 'Spanish', 'Middle Eastern', 'African'
  ];

  // Predefined dietary tags
  const dietaryOptions = [
    'Vegetarian', 'Vegan', 'Gluten-Free', 'Dairy-Free', 
    'Keto', 'Paleo', 'Low-Carb', 'High-Protein',
    'Nut-Free', 'Egg-Free', 'Sugar-Free', 'Low-Sodium',
    'Halal', 'Kosher', 'Pescatarian'
  ];

  const toggleDietaryTag = (tag: string) => {
    setSelectedDietaryTags(prev => 
      prev.includes(tag) 
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const recipeData = {
        title: formData.title,
        raw_text: formData.raw_text,
        cuisine_type: selectedCuisine || undefined,
        dietary_tags: selectedDietaryTags.length > 0 ? selectedDietaryTags : undefined,
        prep_time_minutes: formData.prep_time_minutes ? parseInt(formData.prep_time_minutes) : undefined,
        cook_time_minutes: formData.cook_time_minutes ? parseInt(formData.cook_time_minutes) : undefined,
        servings: formData.servings ? parseInt(formData.servings) : undefined,
      };

      const response = await recipeService.create(recipeData);
      navigate(`/recipes/${response.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create recipe');
    } finally {
      setLoading(false);
    }
  };

  const sampleRecipe = `Spaghetti Carbonara

Ingredients:
- 400g spaghetti
- 200g pancetta or bacon, diced
- 4 large eggs
- 100g Parmesan cheese, grated
- 2 cloves garlic, minced
- Salt and black pepper to taste
- 2 tablespoons olive oil

Instructions:
1. Cook spaghetti according to package directions until al dente.
2. While pasta cooks, heat olive oil in a large pan over medium heat.
3. Add pancetta and cook until crispy, about 5 minutes.
4. Add garlic and cook for 1 minute.
5. In a bowl, whisk eggs and Parmesan cheese together.
6. Drain pasta, reserving 1 cup of pasta water.
7. Add hot pasta to the pan with pancetta.
8. Remove from heat and quickly stir in egg mixture.
9. Add pasta water gradually to achieve creamy consistency.
10. Season with salt and pepper, serve immediately.

Serves: 4`;

  return (
    <div>
      <Navbar />
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Add New Recipe</h1>

        <form onSubmit={handleSubmit} className="space-y-6 bg-white p-6 rounded-lg shadow-md">
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700">
              Recipe Title
            </label>
            <input
              type="text"
              id="title"
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="e.g., Spaghetti Carbonara"
            />
          </div>

          <div>
            <label htmlFor="raw_text" className="block text-sm font-medium text-gray-700">
              Recipe Text
            </label>
            <textarea
              id="raw_text"
              required
              rows={15}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500"
              value={formData.raw_text}
              onChange={(e) => setFormData({ ...formData, raw_text: e.target.value })}
              placeholder={sampleRecipe}
            />
            <p className="mt-2 text-sm text-gray-500">
              Include ingredients list and cooking instructions. The system will parse this automatically.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Cuisine Type (optional) - Select one
            </label>
            <div className="flex flex-wrap gap-2">
              {cuisineTypes.map(cuisine => (
                <button
                  key={cuisine}
                  type="button"
                  onClick={() => setSelectedCuisine(selectedCuisine === cuisine ? '' : cuisine)}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                    selectedCuisine === cuisine
                      ? 'bg-green-600 text-white shadow-md transform scale-105'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {cuisine}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Dietary Tags (optional) - Select all that apply
            </label>
            <div className="flex flex-wrap gap-2">
              {dietaryOptions.map(tag => (
                <button
                  key={tag}
                  type="button"
                  onClick={() => toggleDietaryTag(tag)}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                    selectedDietaryTags.includes(tag)
                      ? 'bg-green-600 text-white shadow-md transform scale-105'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {selectedDietaryTags.includes(tag) && (
                    <span className="mr-1">✓</span>
                  )}
                  {tag}
                </button>
              ))}
            </div>
            {selectedDietaryTags.length > 0 && (
              <p className="mt-2 text-sm text-green-600">
                Selected: {selectedDietaryTags.join(', ')}
              </p>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="prep_time" className="block text-sm font-medium text-gray-700">
                Prep Time (minutes)
              </label>
              <input
                type="number"
                id="prep_time"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500"
                value={formData.prep_time_minutes}
                onChange={(e) => setFormData({ ...formData, prep_time_minutes: e.target.value })}
                placeholder="15"
              />
            </div>

            <div>
              <label htmlFor="cook_time" className="block text-sm font-medium text-gray-700">
                Cook Time (minutes)
              </label>
              <input
                type="number"
                id="cook_time"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500"
                value={formData.cook_time_minutes}
                onChange={(e) => setFormData({ ...formData, cook_time_minutes: e.target.value })}
                placeholder="20"
              />
            </div>

            <div>
              <label htmlFor="servings" className="block text-sm font-medium text-gray-700">
                Servings
              </label>
              <input
                type="number"
                id="servings"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500"
                value={formData.servings}
                onChange={(e) => setFormData({ ...formData, servings: e.target.value })}
                placeholder="4"
              />
            </div>
          </div>

          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={() => navigate('/')}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Recipe'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RecipeForm;