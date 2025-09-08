import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { recipeService } from '../services/api';

const RecipeForm: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [inputType, setInputType] = useState<'text' | 'url' | 'image'>('text');
  const [selectedCuisine, setSelectedCuisine] = useState('');
  const [selectedDietaryTags, setSelectedDietaryTags] = useState<string[]>([]);
  const [formData, setFormData] = useState({
    title: '',
    raw_text: '',
    recipe_url: '',
    prep_time_minutes: '',
    cook_time_minutes: '',
    servings: '',
  });
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [preserveOriginal, setPreserveOriginal] = useState(false);

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

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        setError('Please select an image file');
        return;
      }
      
      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        setError('Image size must be less than 10MB');
        return;
      }
      
      setSelectedImage(file);
      
      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const removeImage = () => {
    setSelectedImage(null);
    setImagePreview(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (inputType === 'image') {
        // Handle image upload
        if (!selectedImage) {
          setError('Please select an image to upload');
          setLoading(false);
          return;
        }

        const formDataToSend = new FormData();
        formDataToSend.append('file', selectedImage);
        
        // Add optional metadata
        if (formData.title) formDataToSend.append('title', formData.title);
        if (selectedCuisine) formDataToSend.append('cuisine_type', selectedCuisine);
        console.log('DEBUG: preserveOriginal value:', preserveOriginal, 'toString:', preserveOriginal.toString());
        formDataToSend.append('preserve_original', preserveOriginal.toString());
        if (selectedDietaryTags.length > 0) {
          selectedDietaryTags.forEach(tag => formDataToSend.append('dietary_tags', tag));
        }
        if (formData.prep_time_minutes) formDataToSend.append('prep_time_minutes', formData.prep_time_minutes);
        if (formData.cook_time_minutes) formDataToSend.append('cook_time_minutes', formData.cook_time_minutes);
        if (formData.servings) formDataToSend.append('servings', formData.servings);

        const response = await recipeService.createFromImage(formDataToSend);
        navigate(`/recipes/${response.id}`);
      } else {
        // Handle text or URL input
        const recipeText = inputType === 'url' ? formData.recipe_url : formData.raw_text;
        
        if (!recipeText) {
          setError(inputType === 'url' ? 'Please enter a recipe URL' : 'Please enter recipe text');
          setLoading(false);
          return;
        }

        const recipeData = {
          title: formData.title,
          raw_text: recipeText, // Backend will detect if it's a URL
          preserve_original: preserveOriginal,
          cuisine_type: selectedCuisine || undefined,
          dietary_tags: selectedDietaryTags.length > 0 ? selectedDietaryTags : undefined,
          prep_time_minutes: formData.prep_time_minutes ? parseInt(formData.prep_time_minutes) : undefined,
          cook_time_minutes: formData.cook_time_minutes ? parseInt(formData.cook_time_minutes) : undefined,
          servings: formData.servings ? parseInt(formData.servings) : undefined,
        };

        const response = await recipeService.create(recipeData);
        navigate(`/recipes/${response.id}`);
      }
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
              Recipe Title {inputType === 'url' && <span className="text-gray-500 font-normal">(optional - will be extracted from URL)</span>}
            </label>
            <input
              type="text"
              id="title"
              required={inputType === 'text'}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder={inputType === 'url' ? "Leave blank to use title from website" : "e.g., Spaghetti Carbonara"}
            />
          </div>

          <div>
            <div className="flex items-center space-x-4 mb-4">
              <button
                type="button"
                onClick={() => setInputType('text')}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  inputType === 'text'
                    ? 'bg-green-600 text-white shadow-md'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Enter Recipe Text
              </button>
              <button
                type="button"
                onClick={() => setInputType('url')}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  inputType === 'url'
                    ? 'bg-green-600 text-white shadow-md'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Import from URL
              </button>
              <button
                type="button"
                onClick={() => setInputType('image')}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  inputType === 'image'
                    ? 'bg-green-600 text-white shadow-md'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Upload Image
              </button>
            </div>

            {inputType === 'text' ? (
              <>
                <label htmlFor="raw_text" className="block text-sm font-medium text-gray-700">
                  Recipe Text
                </label>
                <textarea
                  id="raw_text"
                  required={inputType === 'text'}
                  rows={15}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500"
                  value={formData.raw_text}
                  onChange={(e) => setFormData({ ...formData, raw_text: e.target.value })}
                  placeholder={sampleRecipe}
                />
                <p className="mt-2 text-sm text-gray-500">
                  Include ingredients list and cooking instructions. The system will parse this automatically.
                </p>
              </>
            ) : inputType === 'url' ? (
              <>
                <label htmlFor="recipe_url" className="block text-sm font-medium text-gray-700">
                  Recipe URL
                </label>
                <input
                  type="url"
                  id="recipe_url"
                  required={inputType === 'url'}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500"
                  value={formData.recipe_url}
                  onChange={(e) => setFormData({ ...formData, recipe_url: e.target.value })}
                  placeholder="https://www.example.com/recipe-page"
                />
                <p className="mt-2 text-sm text-gray-500">
                  Paste a URL from any recipe website. We'll automatically extract and analyze the recipe.
                </p>
              </>
            ) : (
              <>
                <label className="block text-sm font-medium text-gray-700">
                  Recipe Image
                </label>
                {!imagePreview ? (
                  <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md hover:border-green-400 transition-colors">
                    <div className="space-y-1 text-center">
                      <svg
                        className="mx-auto h-12 w-12 text-gray-400"
                        stroke="currentColor"
                        fill="none"
                        viewBox="0 0 48 48"
                      >
                        <path
                          d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                          strokeWidth={2}
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                      <div className="flex text-sm text-gray-600">
                        <label
                          htmlFor="file-upload"
                          className="relative cursor-pointer bg-white rounded-md font-medium text-green-600 hover:text-green-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-green-500"
                        >
                          <span>Upload a file</span>
                          <input
                            id="file-upload"
                            name="file-upload"
                            type="file"
                            className="sr-only"
                            accept="image/*"
                            onChange={handleImageChange}
                            required={inputType === 'image'}
                          />
                        </label>
                        <p className="pl-1">or drag and drop</p>
                      </div>
                      <p className="text-xs text-gray-500">
                        PNG, JPG, GIF up to 10MB
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="mt-1 relative">
                    <img
                      src={imagePreview}
                      alt="Recipe preview"
                      className="w-full max-h-96 object-contain rounded-md border border-gray-300"
                    />
                    <button
                      type="button"
                      onClick={removeImage}
                      className="absolute top-2 right-2 bg-red-500 text-white rounded-full p-2 hover:bg-red-600 shadow-lg"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                )}
                <p className="mt-2 text-sm text-gray-500">
                  Upload a photo of a handwritten recipe or a page from a recipe book. We'll extract and analyze the text automatically.
                </p>
              </>
            )}
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

          <div className="bg-blue-50 p-4 rounded-lg">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={preserveOriginal}
                onChange={(e) => setPreserveOriginal(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">
                Preserve Original Recipe Text
              </span>
            </label>
            <p className="mt-1 text-xs text-gray-600 ml-6">
              When checked, the recipe instructions will be kept exactly as written without any modifications or improvements
            </p>
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
              {loading ? (
                inputType === 'url' ? 'Fetching & Analyzing...' : 
                inputType === 'image' ? 'Processing Image...' : 
                'Creating...'
              ) : 'Create Recipe'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RecipeForm;