fn main() {
    // ---------- 1. 变量与可变性 ----------
    let x = 5;          // 默认不可变
    let mut y = 10;     // mut 关键字使其可变
    y += 1;
    println!("x={x}, y={y}");

    // ---------- 2. 基本数据类型 ----------
    let _a: i32 = -42;           // 有符号整数
    let _b: u32 = 100;           // 无符号整数
    let _c: f64 = 3.14;          // 浮点数
    let _d: bool = true;         // 布尔值
    let _e: char = 'R';          // 字符（4字节，支持 Unicode）
    let _s: &str = "hello";      // 字符串切片

    // ---------- 3. 字符串 ----------
    let mut s = String::from("Hello");
    s.push_str(", Rust!");
    println!("{s}");

    // ---------- 4. 函数 ----------
    let sum = add(3, 5);
    println!("3 + 5 = {sum}");

    // ---------- 5. if/else ----------
    let grade = 85;
    if grade >= 60 {
        println!("及格");
    } else {
        println!("不及格");
    }

    // ---------- 6. 循环 ----------
    for i in 0..3 {
        println!("循环 {i}");
    }

    // ---------- 7. match 匹配 ----------
    let number = 2;
    match number {
        1 => println!("一"),
        2 => println!("二"),
        _ => println!("其他"),
    }

    // ---------- 8. 向量 (动态数组) ----------
    let mut v = vec![1, 2, 3];
    v.push(4);
    for val in &v {
        print!("{val} ");
    }
    println!();

    // ---------- 9. Option 与错误处理 ----------
    let maybe = divide(10.0, 2.0);
    match maybe {
        Some(result) => println!("10 / 2 = {result}"),
        None => println!("除数不能为 0"),
    }
}

fn add(a: i32, b: i32) -> i32 {
    a + b // 最后一个表达式就是返回值（无分号）
}

fn divide(a: f64, b: f64) -> Option<f64> {
    if b == 0.0 {
        None
    } else {
        Some(a / b)
    }
}
