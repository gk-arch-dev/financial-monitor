import './Footer.css';

export default function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="footer">
      <span>Sources: Treasury.gov · ECB · BOJ · RBI · Banco Central · Updated every 15 min</span>
      <span>Financial Monitor © {year}</span>
    </footer>
  );
}
