#include <iostream>
#include <cstring>
#include <algorithm>
using namespace std;
const int N = 510;

int dp[N][N];
int n;


int main() {
    cin >> n;
    for (int i = 1; i <= n; i++) {
        for (int j = 1; j <= i; j++) {
            cin >> dp[i][j];
        }
    }
    
    for (int i = 1; i <= n; i++) {
        for (int j = 1; j <= i; j++) {
            if (j == 1)
                dp[i][j] = dp[i-1][j] + dp[i][j];
            else if (i == j)
                dp[i][j] = dp[i-1][j-1] + dp[i][j];
            else
                dp[i][j] = max(dp[i-1][j-1], dp[i-1][j]) + dp[i][j];
        }
    }
    int res = dp[n][1];
    for (int i = 1; i <= n; i++) {
        res = max(res, dp[n][i]);
    }
    cout << res << endl;
    return 0;
}
