#include <cstdio>
#include <iostream>
#include <algorithm>
using namespace std;

int arr[100005];

void quick_sort(int l, int r) {
    if (l >= r) return;
    int i = l - 1; int j = r + 1; int m = (r + l) / 2;
    int pivot = arr[m];
    while (i < j) {
        while (arr[++i] < pivot) ;
        while (arr[--j] > pivot) ;
        if (i < j) {
            swap(arr[i], arr[j]);
        }
    }
    quick_sort(l, j);
    quick_sort(j + 1, r);
}

int main() {
    int n;
    scanf("%d", &n);
    for (int i = 0; i < n; i++) {
        scanf("%d", &arr[i]);
    }
    quick_sort(0, n - 1);
    for (int i = 0; i < n; i++) {
        printf("%d ", arr[i]);
    }
    return 0;
}
