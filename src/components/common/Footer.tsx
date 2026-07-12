import React from 'react';

export default function Footer() {
  return (
    <footer className="w-full py-6 px-4 bg-transparent mt-auto">
      <div className="max-w-7xl mx-auto flex flex-col items-center justify-center gap-3">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-bold text-slate-400 tracking-[0.2em] uppercase">
            Powered By Razel Tech 2026
          </span>
          <div className="flex items-center shadow-sm rounded-[1px] overflow-hidden border border-slate-200">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 600" className="w-5 h-3">
              <rect width="900" height="200" fill="#FF9933"/>
              <rect y="200" width="900" height="200" fill="#ffffff"/>
              <rect y="400" width="900" height="200" fill="#128807"/>
              <circle cx="450" cy="300" r="70" fill="none" stroke="#000080" strokeWidth="8"/>
              <circle cx="450" cy="300" r="15" fill="#000080"/>
            </svg>
          </div>
        </div>
      </div>
    </footer>
  );
}
