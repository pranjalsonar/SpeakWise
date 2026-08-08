import "./Navbar.css";
function Navbar() {
  return (
    <nav>
      <div>SpeakWise</div>
  <ul>
    <li>
      <a href="#home">Home</a>
    </li>
    <li>
      <a href="#features">Features</a>
    </li>
    <li>
      <a href="#about">About</a>
    </li>
    <li>
      <a href="#contact">Contact</a>
    </li>
  </ul>

  <button type="button">Get Started</button>
</nav>
  );
}
export default Navbar;