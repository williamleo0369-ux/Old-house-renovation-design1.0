import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Home() {
  const [image, setImage] = useState(null);
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const reader = new FileReader();
      reader.onloadend = () => {
        setImage(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      const reader = new FileReader();
      reader.onloadend = () => {
        setImage(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleStartRenovation = () => {
    if (!image) return;
    navigate('/constraints', { state: { image } });
  };


  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
      <div className="w-full max-w-2xl p-8 space-y-8 bg-white rounded-lg shadow-md">
        <h1 className="text-4xl font-bold text-center text-gray-800">AI 旧房改造</h1>
        <p className="text-center text-gray-600">上传一张您想要改造的房间照片，AI 将为您生成惊艳的效果图！</p>
        <div 
          className="flex items-center justify-center w-full h-64 border-4 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-gray-400"
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => document.getElementById('file-upload').click()}
        >
          {image ? (
            <img src={image} alt="Uploaded preview" className="object-cover w-full h-full rounded-lg"/>
          ) : (
            <div className="text-center">
              <p className="text-gray-500">拖拽或点击此处上传图片</p>
              <p className="text-sm text-gray-400">支持 JPG, PNG, WEBP</p>
            </div>
          )}
          <input id="file-upload" type="file" className="hidden" onChange={handleFileChange} accept="image/*"/>
        </div>
        {image && (
          <div className="flex justify-center">
            <button 
              className="px-6 py-2 mt-4 text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              onClick={handleStartRenovation}
            >
              开始改造
            </button>
          </div>
        )}
      </div>
    </div>
  );
}