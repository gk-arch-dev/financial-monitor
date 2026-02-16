import Header from '@shared/components/Header';
import Footer from '@shared/components/Footer';
import BondSpreadsDashboard from '@features/bond-spreads/components/BondSpreadsDashboard';

import '@features/bond-spreads/styles/bond-spreads.css';
import './App.css';

function App() {
  return (
    <div className="app">
      <div className="container">
        <Header />
        <main>
          <BondSpreadsDashboard />
        </main>
        <Footer />
      </div>
    </div>
  );
}

export default App;
