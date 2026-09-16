"""Per-language starter code for the three demo MAIN questions.

For the DEBUGGING question the starters are deliberately BROKEN (off-by-one);
for MATH and LEETCODE they are TODO stubs. Extracted verbatim from seed.py.
"""
# ─────────────────────────────────────────────────────────────────────────────
# Q1 - DEBUGGING: the code runs but is wrong. Fix it.
# ─────────────────────────────────────────────────────────────────────────────

DEBUG_STARTER = {
    "python": (
        "# Sum of every integer from 1 to n.\n"
        "# This solution is WRONG - fix it.\n"
        "n = int(input())\n"
        "total = 0\n"
        "for i in range(1, n):\n"
        "    total += i\n"
        "print(total)\n"
    ),
    "c": (
        "#include <stdio.h>\n"
        "int main(void) {\n"
        "    int n; scanf(\"%d\", &n);\n"
        "    int total = 0;\n"
        "    for (int i = 1; i < n; i++) total += i;\n"
        "    printf(\"%d\\n\", total);\n"
        "    return 0;\n"
        "}\n"
    ),
    "cpp": (
        "#include <iostream>\n"
        "using namespace std;\n"
        "int main() {\n"
        "    int n; cin >> n;\n"
        "    int total = 0;\n"
        "    for (int i = 1; i < n; i++) total += i;\n"
        "    cout << total << endl;\n"
        "    return 0;\n"
        "}\n"
    ),
    "java": (
        "import java.util.Scanner;\n"
        "public class Main {\n"
        "    public static void main(String[] args) {\n"
        "        Scanner sc = new Scanner(System.in);\n"
        "        int n = sc.nextInt();\n"
        "        int total = 0;\n"
        "        for (int i = 1; i < n; i++) total += i;\n"
        "        System.out.println(total);\n"
        "    }\n"
        "}\n"
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# Q2 - MATH: implement from scratch. Compared with float tolerance.
# ─────────────────────────────────────────────────────────────────────────────

MATH_STARTER = {
    "python": (
        "# Compound interest: A = P * (1 + r) ** t\n"
        "# Read P, r and t, one per line. Print A to 2 decimal places.\n"
        "p = float(input())\n"
        "r = float(input())\n"
        "t = float(input())\n"
        "\n"
        "# TODO: implement\n"
        "print(\"0.00\")\n"
    ),
    "c": (
        "#include <stdio.h>\n"
        "#include <math.h>\n"
        "int main(void) {\n"
        "    double p, r, t;\n"
        "    scanf(\"%lf %lf %lf\", &p, &r, &t);\n"
        "    /* TODO: compute A = p * pow(1 + r, t) */\n"
        "    printf(\"%.2f\\n\", 0.0);\n"
        "    return 0;\n"
        "}\n"
    ),
    "cpp": (
        "#include <iostream>\n"
        "#include <iomanip>\n"
        "#include <cmath>\n"
        "using namespace std;\n"
        "int main() {\n"
        "    double p, r, t;\n"
        "    cin >> p >> r >> t;\n"
        "    // TODO: compute A = p * pow(1 + r, t)\n"
        "    cout << fixed << setprecision(2) << 0.0 << endl;\n"
        "    return 0;\n"
        "}\n"
    ),
    "java": (
        "import java.util.Scanner;\n"
        "public class Main {\n"
        "    public static void main(String[] args) {\n"
        "        Scanner sc = new Scanner(System.in);\n"
        "        double p = sc.nextDouble();\n"
        "        double r = sc.nextDouble();\n"
        "        double t = sc.nextDouble();\n"
        "        // TODO: compute A = p * Math.pow(1 + r, t)\n"
        "        System.out.printf(\"%.2f%n\", 0.0);\n"
        "    }\n"
        "}\n"
    ),
}

LEETCODE_STARTER = {
    "python": (
        "# Two Sum.\n"
        "# Line 1: n        Line 2: n integers        Line 3: target\n"
        "# Print the two 0-based indices i j (i < j) whose values sum to target.\n"
        "n = int(input())\n"
        "nums = list(map(int, input().split()))\n"
        "target = int(input())\n"
        "\n"
        "# TODO: implement\n"
        "print(\"0 1\")\n"
    ),
    "c": (
        "#include <stdio.h>\n"
        "int main(void) {\n"
        "    int n; scanf(\"%d\", &n);\n"
        "    int a[1000];\n"
        "    for (int i = 0; i < n; i++) scanf(\"%d\", &a[i]);\n"
        "    int target; scanf(\"%d\", &target);\n"
        "    /* TODO */\n"
        "    printf(\"0 1\\n\");\n"
        "    return 0;\n"
        "}\n"
    ),
    "cpp": (
        "#include <iostream>\n"
        "#include <vector>\n"
        "using namespace std;\n"
        "int main() {\n"
        "    int n; cin >> n;\n"
        "    vector<int> a(n);\n"
        "    for (int i = 0; i < n; i++) cin >> a[i];\n"
        "    int target; cin >> target;\n"
        "    // TODO\n"
        "    cout << \"0 1\" << endl;\n"
        "    return 0;\n"
        "}\n"
    ),
    "java": (
        "import java.util.Scanner;\n"
        "public class Main {\n"
        "    public static void main(String[] args) {\n"
        "        Scanner sc = new Scanner(System.in);\n"
        "        int n = sc.nextInt();\n"
        "        int[] a = new int[n];\n"
        "        for (int i = 0; i < n; i++) a[i] = sc.nextInt();\n"
        "        int target = sc.nextInt();\n"
        "        // TODO\n"
        "        System.out.println(\"0 1\");\n"
        "    }\n"
        "}\n"
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# Set 2 Starters
# ─────────────────────────────────────────────────────────────────────────────

DEBUG_STARTER_2 = {
    "python": (
        "# Factorial of n (n >= 0).\n"
        "# This solution is WRONG - fix it.\n"
        "n = int(input())\n"
        "fact = 1\n"
        "for i in range(1, n):\n"
        "    fact *= i\n"
        "print(fact)\n"
    ),
    "c": (
        "#include <stdio.h>\n"
        "int main(void) {\n"
        "    int n; scanf(\"%d\", &n);\n"
        "    long long fact = 1;\n"
        "    for (int i = 1; i < n; i++) fact *= i;\n"
        "    printf(\"%lld\\n\", fact);\n"
        "    return 0;\n"
        "}\n"
    ),
    "cpp": (
        "#include <iostream>\n"
        "using namespace std;\n"
        "int main() {\n"
        "    int n; cin >> n;\n"
        "    long long fact = 1;\n"
        "    for (int i = 1; i < n; i++) fact *= i;\n"
        "    cout << fact << endl;\n"
        "    return 0;\n"
        "}\n"
    ),
    "java": (
        "import java.util.Scanner;\n"
        "public class Main {\n"
        "    public static void main(String[] args) {\n"
        "        Scanner sc = new Scanner(System.in);\n"
        "        int n = sc.nextInt();\n"
        "        long fact = 1;\n"
        "        for (int i = 1; i < n; i++) fact *= i;\n"
        "        System.out.println(fact);\n"
        "    }\n"
        "}\n"
    ),
}

MATH_STARTER_2 = {
    "python": (
        "# Area and circumference of a circle given radius r.\n"
        "# Print area and circumference on separate lines, each rounded to 2 decimal places.\n"
        "# Use pi = 3.141592653589793\n"
        "r = float(input())\n"
        "# TODO: implement\n"
        "print(\"0.00\")\n"
        "print(\"0.00\")\n"
    ),
    "c": (
        "#include <stdio.h>\n"
        "int main(void) {\n"
        "    double r; scanf(\"%lf\", &r);\n"
        "    double pi = 3.141592653589793;\n"
        "    /* TODO */\n"
        "    printf(\"%.2f\\n%.2f\\n\", 0.0, 0.0);\n"
        "    return 0;\n"
        "}\n"
    ),
    "cpp": (
        "#include <iostream>\n"
        "#include <iomanip>\n"
        "using namespace std;\n"
        "int main() {\n"
        "    double r; cin >> r;\n"
        "    double pi = 3.141592653589793;\n"
        "    /* TODO */\n"
        "    cout << fixed << setprecision(2) << 0.0 << endl << 0.0 << endl;\n"
        "    return 0;\n"
        "}\n"
    ),
    "java": (
        "import java.util.Scanner;\n"
        "public class Main {\n"
        "    public static void main(String[] args) {\n"
        "        Scanner sc = new Scanner(System.in);\n"
        "        double r = sc.nextDouble();\n"
        "        /* TODO */\n"
        "        System.out.printf(\"%.2f%n%.2f%n\", 0.0, 0.0);\n"
        "    }\n"
        "}\n"
    ),
}

LEETCODE_STARTER_2 = {
    "python": (
        "# Maximum Subarray (Kadane's Algorithm).\n"
        "# Line 1: n\n"
        "# Line 2: n space-separated integers\n"
        "# Print the maximum subarray sum.\n"
        "n = int(input())\n"
        "nums = list(map(int, input().split()))\n"
        "# TODO: implement\n"
        "print(0)\n"
    ),
    "c": (
        "#include <stdio.h>\n"
        "int main(void) {\n"
        "    int n; scanf(\"%d\", &n);\n"
        "    int a[1000];\n"
        "    for (int i = 0; i < n; i++) scanf(\"%d\", &a[i]);\n"
        "    /* TODO */\n"
        "    printf(\"0\\n\");\n"
        "    return 0;\n"
        "}\n"
    ),
    "cpp": (
        "#include <iostream>\n"
        "#include <vector>\n"
        "using namespace std;\n"
        "int main() {\n"
        "    int n; cin >> n;\n"
        "    vector<int> a(n);\n"
        "    for (int i = 0; i < n; i++) cin >> a[i];\n"
        "    /* TODO */\n"
        "    cout << 0 << endl;\n"
        "    return 0;\n"
        "}\n"
    ),
    "java": (
        "import java.util.Scanner;\n"
        "public class Main {\n"
        "    public static void main(String[] args) {\n"
        "        Scanner sc = new Scanner(System.in);\n"
        "        int n = sc.nextInt();\n"
        "        int[] a = new int[n];\n"
        "        for (int i = 0; i < n; i++) a[i] = sc.nextInt();\n"
        "        /* TODO */\n"
        "        System.out.println(0);\n"
        "    }\n"
        "}\n"
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# Set 3 Starters
# ─────────────────────────────────────────────────────────────────────────────

DEBUG_STARTER_3 = {
    "python": (
        "# Reverse each word in the sentence preserving word order.\n"
        "# This solution is WRONG - fix it.\n"
        "s = input().strip()\n"
        "words = s.split(' ')\n"
        "print(' '.join(w for w in reversed(words)))\n"
    ),
    "c": (
        "#include <stdio.h>\n"
        "#include <string.h>\n"
        "int main(void) {\n"
        "    char s[1000];\n"
        "    if (fgets(s, sizeof(s), stdin)) {\n"
        "        s[strcspn(s, \"\\r\\n\")] = 0;\n"
        "        printf(\"%s\\n\", s);\n"
        "    }\n"
        "    return 0;\n"
        "}\n"
    ),
    "cpp": (
        "#include <iostream>\n"
        "#include <string>\n"
        "#include <sstream>\n"
        "#include <algorithm>\n"
        "using namespace std;\n"
        "int main() {\n"
        "    string s; getline(cin, s);\n"
        "    cout << s << endl;\n"
        "    return 0;\n"
        "}\n"
    ),
    "java": (
        "import java.util.Scanner;\n"
        "public class Main {\n"
        "    public static void main(String[] args) {\n"
        "        Scanner sc = new Scanner(System.in);\n"
        "        String s = sc.nextLine();\n"
        "        System.out.println(s);\n"
        "    }\n"
        "}\n"
    ),
}

MATH_STARTER_3 = {
    "python": (
        "# N-th Fibonacci number (F_0 = 0, F_1 = 1, F_2 = 1, ...)\n"
        "n = int(input())\n"
        "# TODO: implement\n"
        "print(0)\n"
    ),
    "c": (
        "#include <stdio.h>\n"
        "int main(void) {\n"
        "    int n; scanf(\"%d\", &n);\n"
        "    /* TODO */\n"
        "    printf(\"0\\n\");\n"
        "    return 0;\n"
        "}\n"
    ),
    "cpp": (
        "#include <iostream>\n"
        "using namespace std;\n"
        "int main() {\n"
        "    int n; cin >> n;\n"
        "    /* TODO */\n"
        "    cout << 0 << endl;\n"
        "    return 0;\n"
        "}\n"
    ),
    "java": (
        "import java.util.Scanner;\n"
        "public class Main {\n"
        "    public static void main(String[] args) {\n"
        "        Scanner sc = new Scanner(System.in);\n"
        "        int n = sc.nextInt();\n"
        "        /* TODO */\n"
        "        System.out.println(0);\n"
        "    }\n"
        "}\n"
    ),
}

LEETCODE_STARTER_3 = {
    "python": (
        "# Majority Element (element appearing > n/2 times).\n"
        "# Line 1: n\n"
        "# Line 2: n space-separated integers\n"
        "n = int(input())\n"
        "nums = list(map(int, input().split()))\n"
        "# TODO: implement\n"
        "print(0)\n"
    ),
    "c": (
        "#include <stdio.h>\n"
        "int main(void) {\n"
        "    int n; scanf(\"%d\", &n);\n"
        "    int a[1000];\n"
        "    for (int i = 0; i < n; i++) scanf(\"%d\", &a[i]);\n"
        "    /* TODO */\n"
        "    printf(\"0\\n\");\n"
        "    return 0;\n"
        "}\n"
    ),
    "cpp": (
        "#include <iostream>\n"
        "#include <vector>\n"
        "using namespace std;\n"
        "int main() {\n"
        "    int n; cin >> n;\n"
        "    vector<int> a(n);\n"
        "    for (int i = 0; i < n; i++) cin >> a[i];\n"
        "    /* TODO */\n"
        "    cout << 0 << endl;\n"
        "    return 0;\n"
        "}\n"
    ),
    "java": (
        "import java.util.Scanner;\n"
        "public class Main {\n"
        "    public static void main(String[] args) {\n"
        "        Scanner sc = new Scanner(System.in);\n"
        "        int n = sc.nextInt();\n"
        "        int[] a = new int[n];\n"
        "        for (int i = 0; i < n; i++) a[i] = sc.nextInt();\n"
        "        /* TODO */\n"
        "        System.out.println(0);\n"
        "    }\n"
        "}\n"
    ),
}

