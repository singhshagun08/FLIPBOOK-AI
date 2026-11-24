const Footer = () => {
  return (
    <footer className="w-full border-t border-slate-200 bg-white px-6 py-4">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-2 text-sm text-slate-500 sm:flex-row">
        <p>© {new Date().getFullYear()} FLIPBOOK-AI. All rights reserved.</p>

        <p>
          Designed & Developed by{" "}
          <span className="font-semibold text-violet-700">Shagun Singh</span>
        </p>
      </div>
    </footer>
  );
};

export default Footer;
