import { useLocation } from 'react-router-dom';

export default function Design() {
  const location = useLocation();
  const { design } = location.state || {};

  if (!design) {
    return <div>没有找到设计方案。</div>;
  }

  return (
    <div className="flex flex-col items-center min-h-screen bg-gray-100 p-8">
      <div className="w-full max-w-6xl bg-white rounded-lg shadow-md overflow-hidden">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <h2 className="text-3xl font-bold text-gray-800 p-6">AI 设计效果</h2>
            <img src={design.generatedImageUrl} alt="Generated Design" className="w-full h-auto object-cover"/>
          </div>
          <div className="p-6">
            <h2 className="text-3xl font-bold text-gray-800 mb-6">方案商品清单</h2>
            <div className="space-y-4">
              {design.products.map((product) => (
                <div key={product.id} className="flex items-center p-4 border rounded-lg">
                  <img src={product.imageUrl} alt={product.name} className="w-20 h-20 rounded-md mr-4"/>
                  <div>
                    <h3 className="text-xl font-semibold">{product.name}</h3>
                    <p className="text-gray-600">价格: ${product.price}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-8 text-right">
              <p className="text-2xl font-bold">整包价格: ${design.products.reduce((acc, p) => acc + p.price, 0)}</p>
              <button className="px-8 py-3 mt-4 text-white bg-indigo-600 rounded-lg hover:bg-indigo-700">
                一键下单
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
