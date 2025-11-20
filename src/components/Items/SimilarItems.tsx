import { useState, useEffect } from 'react';
import { Sparkles } from 'lucide-react';
import { api } from '../../utils/api';
import ItemCard from './ItemCard';

interface SimilarItemsProps {
  currentItemId: string;
  limit?: number;
}

interface SimilarItem {
  id: string;
  _id?: string;
  title: string;
  description: string;
  category: string;
  location: string;
  imageUrl: string;
  status: string;
  type: string;
  createdAt: string;
  similarity?: number;
  confidence?: string;
}

const SimilarItems = ({ currentItemId, limit = 6 }: SimilarItemsProps) => {
  const [items, setItems] = useState<SimilarItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [isSemanticResult, setIsSemanticResult] = useState(false);

  useEffect(() => {
    fetchSimilarItems();
  }, [currentItemId]);

  const fetchSimilarItems = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/items/${currentItemId}/similar?limit=${limit}`);
      setItems(response.data.items || []);
      setIsSemanticResult(response.data.semantic || false);
    } catch (error) {
      console.error('Failed to fetch similar items:', error);
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="mt-12 py-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (items.length === 0) {
    return null;
  }

  return (
    <div className="mt-12 border-t border-gray-200 pt-8">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <Sparkles className="h-6 w-6 text-blue-600" />
          <h2 className="text-2xl font-bold text-gray-900">AI-Suggested Similar Items</h2>
        </div>
        {isSemanticResult && (
          <span className="text-xs bg-gradient-to-r from-blue-100 to-purple-100 text-blue-800 px-3 py-1 rounded-full font-medium border border-blue-200">
            AI-Powered Recommendations
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {items.map((item) => (
          <div key={item.id} className="relative">
            <ItemCard item={item} />
            {item.similarity && item.similarity > 0.7 && (
              <div className="absolute top-2 right-2 bg-green-500 text-white text-xs px-2 py-1 rounded-full font-semibold">
                {Math.round(item.similarity * 100)}% Match
              </div>
            )}
          </div>
        ))}
      </div>

      {isSemanticResult && (
        <div className="mt-4 text-center">
          <p className="text-sm text-gray-600">
            These items were selected using advanced AI similarity matching based on embeddings and semantic understanding.
          </p>
        </div>
      )}
    </div>
  );
};

export default SimilarItems;
