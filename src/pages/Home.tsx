import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '@/lib/supabase';

export default function Home() {
  const [imagePreview, setImagePreview] = useState(null);
  const [imageFile, setImageFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleFileSelect = (file) => {
    if (file) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleFileChange = (e) => {
    handleFileSelect(e.target.files[0]);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    handleFileSelect(e.dataTransfer.files[0]);
  };

  const handleStartRenovation = async () => {
    if (!imageFile) return;

    setIsLoading(true);
    const fileName = `${Date.now()}_${imageFile.name}`;
    const { data, error } = await supabase.storage
      .from('renovations')
      .upload(fileName, imageFile);

    if (error) {
      console.error('Error uploading file:', error);
      setIsLoading(false);
      return;
    }

    const { data: { publicUrl } } = supabase.storage
      .from('renovations')
      .getPublicUrl(fileName);

    setIsLoading(false);
    navigate('/constraints', { state: { imagePreview, imageUrl: publicUrl } });
  };


  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
      <div className="w-full max-w-2xl p-8 space-y-8 bg-white rounded-lg shadow-md">
        <h1 className="text-4xl font-bold text-center text-gray-800">AI 旧房改造</h1>
        <p className="text-center text-gray-600">上传一张您想要改造的房间照片，AI 将为您生成惊艳的效果图！</p>
        <div 
          className="relative flex items-center justify-center w-full h-64 border-4 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-gray-400"
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => !isLoading && document.getElementById('file-upload').click()}
        >
          {imagePreview ? (
            <img src={imagePreview} alt="Uploaded preview" className="object-cover w-full h-full rounded-lg"/>
          ) : (
            <div className="text-center">
              <p className="text-gray-500">拖拽或点击此处上传图片</p>
              <p className="text-sm text-gray-400">支持 JPG, PNG, WEBP</p>
            </div>
          )}
          <input id="file-upload" type="file" className="hidden" onChange={handleFileChange} accept="image/*" disabled={isLoading}/>
        </div>
        {imagePreview && (
          <div className="flex justify-center">
            <button 
              className="px-6 py-2 mt-4 text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
              onClick={handleStartRenovation}
              disabled={isLoading}
            >
              {isLoading ? '正在上传...' : '开始改造'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}