import rivergen as rg

def main():
    cfile = rg.ConfigFile("configs/farao.yaml")
    exporter = cfile.export()

    exporter.export_to_file()
    #exporter.plot_triangulation()

if __name__ == "__main__":
    import time
    start_time = time.time()
    main()
    print(f"--- {(time.time() - start_time):.3f} seconds ---")