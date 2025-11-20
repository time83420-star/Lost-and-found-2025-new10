import React, { useState, useEffect, useCallback } from 'react';
import { Search, Filter } from 'lucide-react';
import { api } from '../utils/api';
import { useToast } from '../context/ToastContext';
import ItemCard from '../components/Items/ItemCard';
import FilterPanel from '../components/Search/FilterPanel';

interface Item {
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
}

const BrowseItems: React.FC = () => {
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedLocation, setSelectedLocation] = useState('');
  const [selectedType, setSelectedType] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [useSemanticSearch, setUseSemanticSearch] = useState(true);
  const [isSemanticResult, setIsSemanticResult] = useState(false);
  const { showToast } = useToast();

  // ensure frontend items always have an `id` string
  const normalizeItems = (rawItems: any[] = []): Item[] =>
    rawItems.map((i, idx) => {
      const id = String(i.id ?? i._id ?? `generated-${idx}`);
      return { ...i, id } as Item;
    });

  const fetchItems = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedCategory) params.append('category', selectedCategory);
      if (selectedLocation) params.append('location', selectedLocation);
      if (selectedType) params.append('type', selectedType);

      const response = await api.get(`/items?${params.toString()}`);
      console.log('fetchItems raw response:', response.data);

      const normalized = normalizeItems(response.data.items || []);
      setItems(normalized);
    } catch (error: any) {
      console.error('fetchItems error:', error?.response?.data ?? error);
      showToast(error?.response?.data?.message || 'Failed to fetch items', 'error');
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [selectedCategory, selectedLocation, selectedType, showToast]);

  // initial load and refetch when filters change
  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  // Listen for updates from Dashboard
  useEffect(() => {
    const onItemUpdated = (e: Event) => {
      try {
        const ce = e as CustomEvent<any>;
        const detail = ce.detail;
        console.log('BrowseItems received itemUpdated detail:', detail);
        if (!detail) return;

        // If sender explicitly requests a refetch, do that (authoritative)
        if (detail.refetch) {
          console.log('itemUpdated requested refetch — calling fetchItems()');
          fetchItems();
          return;
        }

        // collect candidate ids
        const candidateIds = new Set<string>();
        if (detail.id) candidateIds.add(String(detail.id));
        if (detail._id) candidateIds.add(String(detail._id));
        if (detail.item && (detail.item.id || detail.item._id)) {
          if (detail.item.id) candidateIds.add(String(detail.item.id));
          if (detail.item._id) candidateIds.add(String(detail.item._id));
        }

        if (candidateIds.size === 0) {
          console.warn('itemUpdated detail had no id/_id to match (and no refetch):', detail);
          return;
        }

        const updatedStatus = detail.status as string | undefined;

        // update any matching item
        setItems((prev) =>
          prev.map((it) => {
            const itId = it.id;
            const itAlt = it._id ?? '';
            if (candidateIds.has(itId) || (itAlt && candidateIds.has(itAlt))) {
              console.log(`Matched item ${itId} (alt ${itAlt}) — setting status to`, updatedStatus);
              return { ...it, ...(updatedStatus ? { status: updatedStatus } : {}) };
            }
            return it;
          })
        );
      } catch (err) {
        console.error('onItemUpdated handler error', err);
      }
    };

    window.addEventListener('itemUpdated', onItemUpdated as EventListener);
    return () => window.removeEventListener('itemUpdated', onItemUpdated as EventListener);
  }, [fetchItems]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setLoading(true);
    setIsSemanticResult(false);
    try {
      const response = await api.post('/items/search', {
        query: searchQuery,
        useSemanticSearch: useSemanticSearch
      });
      console.log('search raw response:', response.data);
      const normalized = normalizeItems(response.data.items || []);
      setItems(normalized);
      setIsSemanticResult(response.data.semantic || false);

      if (response.data.semantic) {
        showToast('AI-powered semantic search results', 'success');
      }
    } catch (error: any) {
      console.error('search error:', error?.response?.data ?? error);
      showToast(error?.response?.data?.message || 'Search failed', 'error');
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Browse Items</h1>

        <form onSubmit={handleSearch} className="space-y-3 mb-4">
          <div className="flex space-x-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search items (e.g., 'blue backpack near library')"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <button
              type="submit"
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
            >
              <Search className="h-5 w-5" />
              <span>Search</span>
            </button>
            <button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 transition-colors"
            >
              <Filter className="h-5 w-5" />
            </button>
          </div>

          <div className="flex items-center space-x-3">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={useSemanticSearch}
                onChange={(e) => setUseSemanticSearch(e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Use AI-powered semantic search</span>
            </label>
            {isSemanticResult && (
              <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full font-medium">
                Semantic Results
              </span>
            )}
          </div>
        </form>

        {showFilters && (
          <FilterPanel
            selectedCategory={selectedCategory}
            setSelectedCategory={setSelectedCategory}
            selectedLocation={selectedLocation}
            setSelectedLocation={setSelectedLocation}
            selectedType={selectedType}
            setSelectedType={setSelectedType}
          />
        )}
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-600 text-lg">No items found</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {items.map((item) => (
            <ItemCard key={item.id} item={item} />
          ))}
        </div>
      )}
    </div>
  );
};

export default BrowseItems;
