void state_update_struc(unsigned int state[4], const unsigned int key[4])
{
  unsigned int number_of_steps = 128 * 8;
  unsigned int i;
  unsigned int t1, t2, t3, t4, feedback;
  for (i = 0; i < (number_of_steps >> 5); i++)
  {
    t1 = (state[1] >> 15) | (state[2] << 17);
    t2 = (state[2] >> 6) | (state[3] << 26);
    t3 = (state[2] >> 21) | (state[3] << 11);
    t4 = (state[2] >> 27) | (state[3] << 5);
    feedback = state[0] ^ t1 ^ (~(t2 & t3)) ^ t4 ^ key[i & 3];
    state[0] = state[1];
    state[1] = state[2];
    state[2] = state[3];
    state[3] = feedback;
  }
}
