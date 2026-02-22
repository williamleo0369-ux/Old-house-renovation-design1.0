import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

export default function Constraints() {
  const location = useLocation();
  const navigate = useNavigate();
  const { image } = location.state || {};

  const [constraints, setConstraints] = useState({
    plumbing: false,
    flooring: true,
  });

  if (!image) {
    return <div>没有找到图片，请返回首页重新上传。</div>;
  }

  const handleConstraintChange = (key, value) => {
    setConstraints(prev => ({ ...prev, [key]: value }));
  };

  const handleGenerateDesign = async () => {
    const response = await fetch('/api/renovations', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        imageUrl: 'https://example.com/user_upload.jpg', // 模拟的图片 URL
        constraints,
      }),
    });

    if (response.ok) {
      const data = await response.json();
      navigate('/design', { state: { design: data } });
    } else {
      console.error('Failed to create renovation');
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
      <div className="w-full max-w-2xl p-8 space-y-8 bg-white rounded-lg shadow-md">
        <h1 className="text-3xl font-bold text-center text-gray-800">选择工程边界</h1>
        <p className="text-center text-gray-600">请根据您的实际需求，选择以下改造限制</p>
        <div className="space-y-6">
          <div className="flex items-center justify-between p-4 border rounded-lg">
            <label htmlFor="plumbing-toggle" className="text-lg font-medium text-gray-700">是否改动水电？</label>
            <button
              id="plumbing-toggle"
              onClick={() => handleConstraintChange('plumbing', !constraints.plumbing)}
              className={`relative inline-flex items-center h-6 rounded-full w-11 transition-colors duration-200 ease-in-out ${constraints.plumbing ? 'bg-indigo-600' : 'bg-gray-200'}`}>
              <span className={`inline-block w-4 h-4 transform bg-white rounded-full transition-transform duration-200 ease-in-out ${constraints.plumbing ? 'translate-x-6' : 'translate-x-1'}`} />
            </button>
          </div>
          <div className="flex items-center justify-between p-4 border rounded-lg">
            <label htmlFor="flooring-toggle" className="text-lg font-medium text-gray-700">是否保留原有地板？</label>
            <button
              id="flooring-toggle"
              onClick={() => handleConstraintChange('flooring', !constraints.flooring)}
              className={`relative inline-flex items-center h-6 rounded-full w-11 transition-colors duration-200 ease-in-out ${constraints.flooring ? 'bg-indigo-600' : 'bg-gray-200'}`}>
              <span className={`inline-block w-4 h-4 transform bg-white rounded-full transition-transform duration-200 ease-in-out ${constraints.flooring ? 'translate-x-6' : 'translate-x-1'}`} />
            </button>
          </div>
        </div>
        <div className="flex justify-center">
          <button 
            className="px-8 py-3 mt-6 text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            onClick={handleGenerateDesign}
          >
            生成设计方案
          </button>
        </div>
      </div>
    </div>
  );
}
