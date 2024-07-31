## 代码

```c frame="auto" {"1":1} {"1":10} {"2":14-20}
#define def_rtl(name, ...) void concat(rtl_, name)(DecodeExecState *s, __VA_ARGS__)

#define def_rtl_compute_reg(name) \
  static inline def_rtl(name, rtlreg_t* dest, const rtlreg_t* src1, const rtlreg_t* src2) { \
    *dest = concat(c_, name) (*src1, *src2); \
  }

#define def_rtl_compute_imm(name) \
  static inline def_rtl(name ## i, rtlreg_t* dest, const rtlreg_t* src1, const sword_t imm) { \
    *dest = concat(c_, name) (*src1, imm); \
  }

#define def_rtl_compute_reg_imm(name) \
  def_rtl_compute_reg(name) \
  def_rtl_compute_imm(name) \

def_rtl_compute_reg_imm(add)
def_rtl_compute_reg_imm(sub)
def_rtl_compute_reg_imm(and)
def_rtl_compute_reg_imm(or)
def_rtl_compute_reg_imm(xor)
def_rtl_compute_reg_imm(shl)
def_rtl_compute_reg_imm(shr)
def_rtl_compute_reg_imm(sar)

#define c_shift_mask 0x1f

#define c_add(a, b) ((a) + (b))
#define c_sub(a, b) ((a) - (b))
#define c_and(a, b) ((a) & (b))
#define c_or(a, b)  ((a) | (b))
#define c_xor(a, b) ((a) ^ (b))
#define c_shl(a, b) ((a) << ((b) & c_shift_mask))
#define c_shr(a, b) ((a) >> ((b) & c_shift_mask))
#define c_sar(a, b) ((sword_t)(a) >> ((b) & c_shift_mask))

```

## 展开 def_rtl_compute_reg_imm(add)

我们以其中的一个函数为例子展开  `{cpp} def_rtl_compute_reg_imm(add)`。

```c hl:11-16
//def_rtl_compute_reg_immadd.c
def_rtl_compute_reg_imm(add)

//***************************

def_rtl_compute_reg(add)
def_rtl_compute_imm(add)

//***************************

static inline def_rtl(add, rtlreg_t* dest, const rtlreg_t* src1, const rtlreg_t* src2) { \
    *dest = c_add(*src1, *src2); \
}
static inline def_rtl(addi, rtlreg_t* dest, const rtlreg_t* src1, const sword_t imm) { \
    *dest = c_add(*src1, imm); \
}

//***************************

static inline void rtl_add(DecodeExecState *s, rtlreg_t* dest, const rtlreg_t* src1, const rtlreg_t* src2) {
    *dest = c_add(*src1, *src2); // *dest = ((*src1) + (*src2));
}
static inline void rtl_addi(DecodeExecState *s, rtlreg_t* dest, const rtlreg_t* src1, const sword_t imm) {
    *dest = c_add(*src1, imm);  // *dest = ((*src1) + (imm));
}
```

### 展开 setrelop

```c
static inline def_rtl(setrelop, uint32_t relop, rtlreg_t *dest, const rtlreg_t *src1, const rtlreg_t *src2) {
  *dest = interpret_relop(relop, *src1, *src2);
}

// 展开后
static inline rtl_setrelop(DecodeExecState *s, uint32_t relop, rtlreg_t *dest, const rtlreg_t *src1, const rtlreg_t *src2) {
  *dest = interpret_relop(relop, *src1, *src2);
}

static inline def_rtl(setrelopi, uint32_t relop, rtlreg_t *dest, const rtlreg_t *src1, sword_t imm) {
  *dest = interpret_relop(relop, *src1, imm);
}

// 展开后
static inline rtl_setrelopi(DecodeExecState *s, uint32_t relop, rtlreg_t *dest, const rtlreg_t *src1, const rtlreg_t *src2) {
  *dest = interpret_relop(relop, *src1, *src2);
}

static inline bool interpret_relop(uint32_t relop, const rtlreg_t src1, const rtlreg_t src2) {
  switch (relop) {
    case RELOP_FALSE: return false;
    case RELOP_TRUE: return true;
    case RELOP_EQ: return src1 == src2;
    case RELOP_NE: return src1 != src2;
    case RELOP_LT: return (sword_t)src1 <  (sword_t)src2;
    case RELOP_LE: return (sword_t)src1 <= (sword_t)src2;
    case RELOP_GT: return (sword_t)src1 >  (sword_t)src2;
    case RELOP_GE: return (sword_t)src1 >= (sword_t)src2;
    case RELOP_LTU: return src1 < src2;
    case RELOP_LEU: return src1 <= src2;
    case RELOP_GTU: return src1 > src2;
    case RELOP_GEU: return src1 >= src2;
    default: panic("unsupport relop = %d", relop);
  }
}
```
