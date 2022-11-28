```txt
main
  |
  +---init_monitor(argc, argv)
  |      |
  |      +---parse_args(argc, argv)
  |      |
  |      +---init_meme()
  |      |
  |      +---init_isa()
  |      |
  |      +---long img_size()=load_img()
  |      |
  |      +---init_regex()
  |      |
  |      +---init_wp_pool()
  |      |
  |      +---init_difftest()
  |      |
  |      +---welcome()
  |
  |
  +---engine_start()
         |
         +---init_device()
         |
         +---ui_mainloop()
```