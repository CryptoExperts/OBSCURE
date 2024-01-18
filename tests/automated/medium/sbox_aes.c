void sbox(const unsigned int in[8], unsigned int out[8]) {
  unsigned int y14 = in[3] ^ in[5];
  unsigned int y13 = in[0] ^ in[6];
  unsigned int y9 = in[0] ^ in[3];
  unsigned int y8 = in[0] ^ in[5];
  unsigned int t0 = in[1] ^ in[2];
  unsigned int y1 = t0 ^ in[7];
  unsigned int y4 = y1 ^ in[3];
  unsigned int y12 = y13 ^ y14;
  unsigned int y2 = y1 ^ in[0];
  unsigned int y5 = y1 ^ in[6];
  unsigned int y3 = y5 ^ y8;
  unsigned int t1 = in[4] ^ y12;
  unsigned int y15 = t1 ^ in[5];
  unsigned int y20 = t1 ^ in[1];
  unsigned int y6 = y15 ^ in[7];
  unsigned int y10 = y15 ^ t0;
  unsigned int y11 = y20 ^ y9;
  unsigned int y7 = in[7] ^ y11;
  unsigned int y17 = y10 ^ y11;
  unsigned int y19 = y10 ^ y8;
  unsigned int y16 = t0 ^ y11;
  unsigned int y21 = y13 ^ y16;
  unsigned int y18 = in[0] ^ y16;
  unsigned int t2 = y12 & y15;
  unsigned int t3 = y3 & y6;
  unsigned int t4 = t3 ^ t2;
  unsigned int t5 = y4 & in[7];
  unsigned int t6 = t5 ^ t2;
  unsigned int t7 = y13 & y16;
  unsigned int t8 = y5 & y1;
  unsigned int t9 = t8 ^ t7;
  unsigned int t10 = y2 & y7;
  unsigned int t11 = t10 ^ t7;
  unsigned int t12 = y9 & y11;
  unsigned int t13 = y14 & y17;
  unsigned int t14 = t13 ^ t12;
  unsigned int t15 = y8 & y10;
  unsigned int t16 = t15 ^ t12;
  unsigned int t17 = t4 ^ y20;
  unsigned int t18 = t6 ^ t16;
  unsigned int t19 = t9 ^ t14;
  unsigned int t20 = t11 ^ t16;
  unsigned int t21 = t17 ^ t14;
  unsigned int t22 = t18 ^ y19;
  unsigned int t23 = t19 ^ y21;
  unsigned int t24 = t20 ^ y18;
  unsigned int t25 = t21 ^ t22;
  unsigned int t26 = t21 & t23;
  unsigned int t27 = t24 ^ t26;
  unsigned int t28 = t25 & t27;
  unsigned int t29 = t28 ^ t22;
  unsigned int t30 = t23 ^ t24;
  unsigned int t31 = t22 ^ t26;
  unsigned int t32 = t31 & t30;
  unsigned int t33 = t32 ^ t24;
  unsigned int t34 = t23 ^ t33;
  unsigned int t35 = t27 ^ t33;
  unsigned int t36 = t24 & t35;
  unsigned int t37 = t36 ^ t34;
  unsigned int t38 = t27 ^ t36;
  unsigned int t39 = t29 & t38;
  unsigned int t40 = t25 ^ t39;
  unsigned int t41 = t40 ^ t37;
  unsigned int t42 = t29 ^ t33;
  unsigned int t43 = t29 ^ t40;
  unsigned int t44 = t33 ^ t37;
  unsigned int t45 = t42 ^ t41;
  unsigned int z0 = t44 & y15;
  unsigned int z1 = t37 & y6;
  unsigned int z2 = t33 & in[7];
  unsigned int z3 = t43 & y16;
  unsigned int z4 = t40 & y1;
  unsigned int z5 = t29 & y7;
  unsigned int z6 = t42 & y11;
  unsigned int z7 = t45 & y17;
  unsigned int z8 = t41 & y10;
  unsigned int z9 = t44 & y12;
  unsigned int z10 = t37 & y3;
  unsigned int z11 = t33 & y4;
  unsigned int z12 = t43 & y13;
  unsigned int z13 = t40 & y5;
  unsigned int z14 = t29 & y2;
  unsigned int z15 = t42 & y9;
  unsigned int z16 = t45 & y14;
  unsigned int z17 = t41 & y8;
  unsigned int tc1 = z15 ^ z16;
  unsigned int tc2 = z10 ^ tc1;
  unsigned int tc3 = z9 ^ tc2;
  unsigned int tc4 = z0 ^ z2;
  unsigned int tc5 = z1 ^ z0;
  unsigned int tc6 = z3 ^ z4;
  unsigned int tc7 = z12 ^ tc4;
  unsigned int tc8 = z7 ^ tc6;
  unsigned int tc9 = z8 ^ tc7;
  unsigned int tc10 = tc8 ^ tc9;
  unsigned int tc11 = tc6 ^ tc5;
  unsigned int tc12 = z3 ^ z5;
  unsigned int tc13 = z13 ^ tc1;
  unsigned int tc14 = tc4 ^ tc12;
  out[3] = tc3 ^ tc11;
  unsigned int tc16 = z6 ^ tc8;
  unsigned int tc17 = z14 ^ tc10;
  unsigned int tc18 = tc13 ^ tc14;
  out[7] = ~(z12 ^ tc18);
  unsigned int tc20 = z15 ^ tc16;
  unsigned int tc21 = tc2 ^ z11;
  out[0] = tc3 ^ tc16;
  out[6] = ~(tc10 ^ tc18);
  out[4] = tc14 ^ out[3];
  out[1] = ~(out[3] ^ tc16);
  unsigned int tc26 = tc17 ^ tc20;
  out[2] = ~(tc26 ^ z17);
  out[5] = tc21 ^ tc17;
}
