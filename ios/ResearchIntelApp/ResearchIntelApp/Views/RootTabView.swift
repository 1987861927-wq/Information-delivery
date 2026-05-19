import SwiftUI

struct RootTabView: View {
    var body: some View {
        TabView {
            TodayView()
                .tabItem {
                    Label("今日", systemImage: "newspaper")
                }

            TopicsView()
                .tabItem {
                    Label("主题", systemImage: "square.grid.2x2")
                }

            SearchView()
                .tabItem {
                    Label("搜索", systemImage: "magnifyingglass")
                }

            FavoritesView()
                .tabItem {
                    Label("收藏", systemImage: "bookmark")
                }

            SettingsView()
                .tabItem {
                    Label("我的", systemImage: "person.crop.circle")
                }
        }
    }
}

#Preview {
    RootTabView()
}
