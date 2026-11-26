import React from "react";
import logo from "../assets/soilsync-logo.png";
export const Brand = ({ className = "" }) => (
  <img className={`soil-logo ${className}`} src={logo} alt="SoilSync" />
);
